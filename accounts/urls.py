from django.urls import path, include
from rest_framework.routers import DefaultRouter
from dj_rest_auth.views import (
    LogoutView, PasswordChangeView, PasswordResetView, PasswordResetConfirmView
)

from .views import (
    RegisterView, VerifyEmailView, ResendVerificationEmailView,
    PasswordResetRequestView, PasswordResetConfirmView,
    SendOTPView, VerifyOTPView, UserViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('resend-verification/', ResendVerificationEmailView.as_view(), name='resend_verification'),
    
    # Password Management
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # 2FA
    path('2fa/send-otp/', SendOTPView.as_view(), name='send_otp'),
    path('2fa/verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    
    # dj-rest-auth URLs (includes login, token/refresh)
    path('', include('dj_rest_auth.urls')),
    
    # User management
    path('', include(router.urls)),
]
