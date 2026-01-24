from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from dj_rest_auth.views import LoginView as DJRestAuthLoginView
from drf_spectacular.utils import extend_schema
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import random
import string

from .models import (
    User, UserProfile, EmailVerification, PasswordReset, OTPToken, AdminUser
)
from .serializers import (
    CustomUserDetailsSerializer, CustomRegisterSerializer,
    EmailVerificationSerializer, ResendVerificationEmailSerializer,
    CustomPasswordChangeSerializer, SendOTPSerializer, VerifyOTPSerializer,
    AdminUserSerializer, AdminUserCreateSerializer
)
from .permissions import IsVerifiedUser, IsAdminUser, IsAgentUser, IsClientUser

User = get_user_model()


class RegisterView(APIView):
    """User registration endpoint."""
    permission_classes = [permissions.AllowAny]
    serializer_class = CustomRegisterSerializer

    def post(self, request):
        serializer = CustomRegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                
                # Verification email will be sent by signal
                return Response({
                    'status': 'success',
                    'message': 'Registration successful. Please check your email to verify your account.',
                    'data': {
                        'email': user.email,
                        'user_type': user.user_type
                    }
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                # Handle database integrity errors (e.g., duplicate email)
                error_message = str(e)
                if 'UNIQUE constraint' in error_message or 'unique' in error_message.lower():
                    return Response({
                        'status': 'error',
                        'message': 'Registration failed',
                        'errors': {'email': ['A user with this email already exists.']}
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Re-raise unexpected errors
                raise
        
        return Response({
            'status': 'error',
            'message': 'Registration failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    """Email verification endpoint."""
    permission_classes = [permissions.AllowAny]
    serializer_class = EmailVerificationSerializer

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                verification = EmailVerification.objects.get(token=serializer.validated_data['token'])
                user = verification.user
                
                # Mark user as verified
                user.is_verified = True
                user.save()
                
                # Mark verification as used
                verification.is_used = True
                verification.save()
                
                return Response({
                    'status': 'success',
                    'message': 'Email verified successfully. You can now login.'
                }, status=status.HTTP_200_OK)
            except EmailVerification.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Verification token not found.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'status': 'error',
            'message': 'Verification failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationEmailView(APIView):
    """Resend verification email endpoint."""
    permission_classes = [permissions.AllowAny]
    serializer_class = ResendVerificationEmailSerializer

    def post(self, request):
        serializer = ResendVerificationEmailSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(email=serializer.validated_data['email'])
                
                # Create new verification token
                verification = EmailVerification.create_for_user(user)
                
                # Send verification email
                self._send_verification_email(user, verification)
                
                return Response({
                    'status': 'success',
                    'message': 'Verification email sent. Please check your email.'
                }, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'User not found.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'status': 'error',
            'message': 'Failed to resend verification email',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def _send_verification_email(self, user, verification):
        """Send verification email to user."""
        subject = 'Verify Your ESSIVI Account'
        verification_link = f"{settings.FRONTEND_URL}/verify-email/?token={verification.token}"
        message = f"""
        Hello {user.first_name},
        
        Please verify your email by clicking the link below:
        {verification_link}
        
        This link will expire in 24 hours.
        
        Best regards,
        ESSIVI Team
        """
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])


class PasswordResetRequestView(APIView):
    """Request password reset endpoint."""
    permission_classes = [permissions.AllowAny]

    @extend_schema(exclude=True)
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({
                'status': 'error',
                'message': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            
            # Create password reset token
            reset_token = PasswordReset.create_for_user(user)
            
            # Send password reset email
            self._send_password_reset_email(user, reset_token)
            
            return Response({
                'status': 'success',
                'message': 'Password reset link sent. Please check your email.'
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            # Return success anyway for security (don't leak if email exists)
            return Response({
                'status': 'success',
                'message': 'If the email exists, you will receive a password reset link.'
            }, status=status.HTTP_200_OK)
    
    def _send_password_reset_email(self, user, reset_token):
        """Send password reset email to user."""
        subject = 'Reset Your ESSIVI Password'
        reset_link = f"{settings.FRONTEND_URL}/reset-password/?token={reset_token.token}"
        message = f"""
        Hello {user.first_name},
        
        Click the link below to reset your password:
        {reset_link}
        
        This link will expire in 1 hour.
        
        If you didn't request this, ignore this email.
        
        Best regards,
        ESSIVI Team
        """
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])


class PasswordResetConfirmView(APIView):
    """Confirm password reset endpoint."""
    permission_classes = [permissions.AllowAny]

    @extend_schema(exclude=True)
    def post(self, request):
        token = request.data.get('token')
        password = request.data.get('password')
        
        if not token or not password:
            return Response({
                'status': 'error',
                'message': 'Token and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            reset_token = PasswordReset.objects.get(token=token)
            
            if not reset_token.is_valid():
                return Response({
                    'status': 'error',
                    'message': 'Reset token has expired or already used.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update password
            user = reset_token.user
            user.set_password(password)
            user.save()
            
            # Mark token as used
            reset_token.is_used = True
            reset_token.save()
            
            return Response({
                'status': 'success',
                'message': 'Password reset successful. You can now login.'
            }, status=status.HTTP_200_OK)
        except PasswordReset.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Invalid reset token.'
            }, status=status.HTTP_400_BAD_REQUEST)


def generate_otp(length=None):
    """Generate a random OTP code."""
    if length is None:
        from django.conf import settings
        length = settings.OTP_LENGTH
    return ''.join(random.choices(string.digits, k=length))


class SendOTPView(APIView):
    """Send OTP for 2FA."""
    permission_classes = [permissions.IsAuthenticated, IsVerifiedUser]
    serializer_class = SendOTPSerializer

    def post(self, request):
        # Users can only send OTP for themselves
        user = request.user
        
        # Generate OTP
        otp_code = generate_otp()
        
        # Create OTP token
        otp_token = OTPToken.create_for_user(user, otp_code)
        
        # Send OTP via email
        self._send_otp_email(user, otp_code)
        
        return Response({
            'status': 'success',
            'message': 'OTP sent to your email.'
        }, status=status.HTTP_200_OK)
    
    def _send_otp_email(self, user, code):
        """Send OTP via email."""
        subject = 'Your ESSIVI 2FA Code'
        message = f"""
        Hello {user.first_name},
        
        Your 2FA code is: {code}
        
        This code will expire in 10 minutes.
        
        If you didn't request this, ignore this email.
        
        Best regards,
        ESSIVI Team
        """
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])


class VerifyOTPView(APIView):
    """Verify OTP for 2FA."""
    permission_classes = [permissions.IsAuthenticated, IsVerifiedUser]
    serializer_class = VerifyOTPSerializer

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            otp = serializer.validated_data['otp']
            user = request.user
            
            # Mark OTP as used
            otp.is_used = True
            otp.save()
            
            # Mark 2FA as enabled for user
            user.two_factor_enabled = True
            user.save()
            
            return Response({
                'status': 'success',
                'message': 'OTP verified successfully. 2FA enabled.'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'status': 'error',
            'message': 'OTP verification failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management.
    - Authenticated users can view/update their own profile
    - Admins can view/manage all users
    """
    serializer_class = CustomUserDetailsSerializer
    permission_classes = [permissions.IsAuthenticated, IsVerifiedUser]
    queryset = User.objects.all()

    def get_queryset(self):
        """Return only verified users, or all users if admin."""
        if self.request.user.user_type == 'admin':
            return User.objects.all()
        return User.objects.filter(is_verified=True)

    def retrieve(self, request, *args, **kwargs):
        """Allow users to view their own profile."""
        if kwargs['pk'] != str(request.user.id) and request.user.user_type != 'admin':
            return Response({
                'status': 'error',
                'message': 'You do not have permission to view this profile.'
            }, status=status.HTTP_403_FORBIDDEN)
        return super().retrieve(request, *args, **kwargs)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsVerifiedUser])
    def me(self, request):
        """Get current user profile."""
        serializer = self.get_serializer(request.user)
        return Response({
            'status': 'success',
            'data': serializer.data
        })

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsVerifiedUser])
    def change_password(self, request):
        """Change user password."""
        serializer = CustomPasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'message': 'Password changed successfully.'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'status': 'error',
            'message': 'Failed to change password',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class AdminUserViewSet(viewsets.ModelViewSet):
    """ViewSet for managing admin users."""
    
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    filter_backends = [__import__('rest_framework.filters', fromlist=['SearchFilter']).SearchFilter]
    search_fields = ['name', 'user__email', 'role']
    ordering_fields = ['created_at', 'name', 'role', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get admin users queryset."""
        from .models import AdminUser
        return AdminUser.objects.all()
    
    def get_serializer_class(self):
        """Return serializer based on action."""
        from .serializers import AdminUserSerializer, AdminUserCreateSerializer
        if self.action == 'create':
            return AdminUserCreateSerializer
        return AdminUserSerializer
    
    def perform_create(self, serializer):
        """Create a new admin user."""
        serializer.save()
    
    def perform_update(self, serializer):
        """Update admin user."""
        admin_user = serializer.save()
        return admin_user
    
    @action(detail=False, methods=['get'])
    def by_role(self, request):
        """Get admins filtered by role."""
        from .models import AdminUser
        role = request.query_params.get('role')
        if role:
            admins = AdminUser.objects.filter(role=role)
            serializer = self.get_serializer(admins, many=True)
            return Response({
                'status': 'success',
                'data': serializer.data
            })
        return Response({
            'status': 'error',
            'message': 'role parameter required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """Get admins filtered by status."""
        from .models import AdminUser
        admin_status = request.query_params.get('status')
        if admin_status:
            admins = AdminUser.objects.filter(status=admin_status)
            serializer = self.get_serializer(admins, many=True)
            return Response({
                'status': 'success',
                'data': serializer.data
            })
        return Response({
            'status': 'error',
            'message': 'status parameter required'
        }, status=status.HTTP_400_BAD_REQUEST)