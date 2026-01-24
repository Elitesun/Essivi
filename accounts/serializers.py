from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from dj_rest_auth.serializers import (
    LoginSerializer, UserDetailsSerializer, PasswordChangeSerializer,
    PasswordResetSerializer, PasswordResetConfirmSerializer
)
from drf_spectacular.utils import extend_schema_field
from django.contrib.auth import get_user_model
from .models import UserProfile, EmailVerification, OTPToken, AdminUser
from typing import TYPE_CHECKING
import string
import random

User = get_user_model()

if TYPE_CHECKING:
    from .models import User as UserType


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extended JWT token serializer with custom claims.
    """
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['email'] = user.email
        token['user_type'] = user.user_type
        token['is_verified'] = user.is_verified
        
        return token


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile with agent_id and client_code."""
    
    class Meta:
        model = UserProfile
        fields = [
            'profile_picture', 'address', 'city', 'latitude', 'longitude',
            'agent_id', 'tricycle_plate', 'hire_date',
            'business_name', 'contact_person', 'client_code'
        ]
        read_only_fields = ['agent_id', 'client_code']


class CustomUserDetailsSerializer(UserDetailsSerializer):
    """Extended user details serializer with profile and user_type."""
    
    profile = UserProfileSerializer(read_only=True)
    
    @extend_schema_field(serializers.CharField)
    def get_full_name(self, obj):
        """Get the full name from the user object."""
        return obj.full_name
    
    full_name = serializers.SerializerMethodField()
    
    class Meta(UserDetailsSerializer.Meta):
        model = User
        fields = [
            'id', 'email', 'phone', 'first_name', 'last_name', 'full_name',
            'user_type', 'is_verified', 'is_active', 'date_joined', 'profile'
        ]
        read_only_fields = ['id', 'email', 'user_type', 'is_verified', 'date_joined']


class CustomLoginSerializer(LoginSerializer):
    """Extended login serializer that disables allauth email verification check."""
    
    def validate(self, attrs):
        """Override to use email instead of username and disable allauth checks."""
        attrs['username'] = attrs.get('email')
        
        # Call parent validate but catch allauth errors
        try:
            result = super().validate(attrs)
            return result
        except Exception as e:
            # If allauth module error, just do basic authentication
            if 'allauth' in str(e):
                from django.contrib.auth import authenticate
                username = attrs.get('username')
                password = attrs.get('password')
                
                user = authenticate(request=self.context.get('request'),
                email=username, password=password)
                
                if not user:
                    raise serializers.ValidationError(('Unable to log in with provided credentials.'))
                
                attrs['user'] = user
                return attrs
            raise
    
    def validate_email_verification_status(self, user, email=None):
        """Override to disable allauth email verification check."""
        # We use custom email verification, so skip this check
        pass


class CustomRegisterSerializer(serializers.Serializer):
    """Registration serializer for new user accounts."""
    
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)
    phone = serializers.CharField(required=False, max_length=20, allow_blank=True)
    user_type = serializers.ChoiceField(choices=['agent', 'client', 'admin'], required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label='Confirm Password'
    )
    
    def validate(self, data):
        """Validate that passwords match."""
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return data
    
    def create(self, validated_data):
        """Create a new user with email-based authentication."""
        password = validated_data.pop('password')
        phone = validated_data.pop('phone', '')
        user = User.objects.create_user(
            email=validated_data['email'],
            password=password,
            user_type=validated_data['user_type'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=phone
        )
        return user


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for email verification."""
    
    token = serializers.UUIDField()
    
    def validate_token(self, value):
        """Validate the verification token."""
        try:
            verification = EmailVerification.objects.get(token=value)
        except EmailVerification.DoesNotExist:
            raise serializers.ValidationError('Invalid verification token.')
        
        if not verification.is_valid():
            raise serializers.ValidationError('Verification token has expired or already used.')
        
        return value


class ResendVerificationEmailSerializer(serializers.Serializer):
    """Serializer for resending verification email."""
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Validate email exists and user is not verified."""
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('User with this email does not exist.')
        
        if user.is_verified:
            raise serializers.ValidationError('This email is already verified.')
        
        return value


class CustomPasswordChangeSerializer(PasswordChangeSerializer):
    """Extended password change serializer."""
    
    def save(self):
        """Save the new password."""
        user = self.context.get('request').user if self.context.get('request') else self.user
        if user:
            user.set_password(self.validated_data['new_password1'])
            user.save()
            return user
        return None


class CustomPasswordResetSerializer(PasswordResetSerializer):
    """Extended password reset serializer."""
    pass


class CustomPasswordResetConfirmSerializer(PasswordResetConfirmSerializer):
    """Extended password reset confirm serializer."""
    pass


class SendOTPSerializer(serializers.Serializer):
    """Serializer for sending OTP."""
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Validate email exists."""
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('User with this email does not exist.')
        return value


class VerifyOTPSerializer(serializers.Serializer):
    """Serializer for verifying OTP."""
    
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)
    
    def validate(self, data):
        """Validate OTP is correct and not expired."""
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError('User with this email does not exist.')
        
        try:
            otp = OTPToken.objects.get(user=user, code=data['code'])
        except OTPToken.DoesNotExist:
            raise serializers.ValidationError('Invalid OTP code.')
        
        if not otp.is_valid():
            raise serializers.ValidationError('OTP has expired or already used.')
        
        data['user'] = user
        data['otp'] = otp
        return data

class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer for AdminUser management."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    
    class Meta:
        model = AdminUser
        fields = [
            'id', 'user_id', 'user_email', 'name', 'role', 'status',
            'last_connection', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user_id', 'user_email', 'last_connection', 'created_at', 'updated_at']


class AdminUserCreateSerializer(serializers.Serializer):
    """Serializer for creating new admin users."""
    
    email = serializers.EmailField()
    name = serializers.CharField(max_length=255)
    password = serializers.CharField(min_length=8, write_only=True, help_text="Admin's login password")
    confirm_password = serializers.CharField(min_length=8, write_only=True, help_text="Confirm the password")
    role = serializers.ChoiceField(choices=['super_admin', 'gestionnaire', 'superviseur'])
    status = serializers.ChoiceField(choices=['actif', 'inactif'], default='actif')
    
    def validate_email(self, value):
        """Validate email is not already registered."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value
    
    def validate(self, data):
        """Validate that passwords match."""
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        # Remove confirm_password from validated_data as we don't need it anymore
        data.pop('confirm_password', None)
        return data
    
    def create(self, validated_data):
        """Create a new admin user with associated User account."""
        email = validated_data['email']
        name = validated_data['name']
        password = validated_data['password']  # Use provided password instead of generating
        role = validated_data['role']
        status = validated_data['status']
        
        # Create User account with provided password
        user = User.objects.create_user(
            email=email,
            password=password,  # Use the password from the form
            user_type='admin',
            first_name=name.split()[0] if name else 'Admin',
            last_name=' '.join(name.split()[1:]) if len(name.split()) > 1 else 'User',
            is_verified=True,
            is_staff=True
        )
        
        # Create AdminUser profile
        admin_user = AdminUser.objects.create(
            user=user,
            name=name,
            role=role,
            status=status
        )
        
        # Return data dict instead of instance for proper serialization
        return {
            'id': str(admin_user.id),
            'user_id': str(admin_user.user.id),
            'user_email': admin_user.user.email,
            'name': admin_user.name,
            'role': admin_user.role,
            'status': admin_user.status,
            'last_connection': admin_user.last_connection,
            'created_at': admin_user.created_at,
            'updated_at': admin_user.updated_at,
            'message': 'Admin created successfully. Can login with provided credentials.'
        }
    
    def to_representation(self, instance):
        """Convert instance to dict if needed."""
        if isinstance(instance, dict):
            return instance
        # If it's an AdminUser model instance, use AdminUserSerializer
        from .models import AdminUser
        if isinstance(instance, AdminUser):
            return AdminUserSerializer(instance).data
        return instance