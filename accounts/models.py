import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import timedelta


class CustomUserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""

    def create_user(self, email, password, user_type, first_name, last_name, **extra_fields):
        """Create and save a regular user."""
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            user_type=user_type,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, first_name='Admin', last_name='User', **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)
        if 'user_type' in extra_fields:
            del extra_fields['user_type']

        return self.create_user(email, password, user_type='admin', first_name=first_name, last_name=last_name, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model for ESSIVI authentication."""
    
    class UserType(models.TextChoices):
        AGENT = 'agent', 'Agent'
        CLIENT = 'client', 'Client'
        ADMIN = 'admin', 'Administrator'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message='Invalid phone number')]
    )
    user_type = models.CharField(max_length=20, choices=UserType.choices)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    
    # Account status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False, help_text='Email verified')
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    # 2FA Fields
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True, null=True)
    
    # Timestamps
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['user_type', 'first_name', 'last_name']
    
    class Meta:
        ordering = ['-date_joined']
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['user_type']),
            models.Index(fields=['is_verified']),
        ]
    
    # def __str__(self):
    #     return f"{self.email} ({self.get_user_type_display()})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class UserProfile(models.Model):
    """Extended user profile with GPS and profile picture."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profile_pictures/%Y/%m/%d/', null=True, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Agent-specific
    agent_id = models.CharField(max_length=50, unique=True, null=True, blank=True, db_index=True)
    tricycle_plate = models.CharField(max_length=50, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    
    # Client-specific
    business_name = models.CharField(max_length=255, blank=True)
    contact_person = models.CharField(max_length=255, blank=True)
    client_code = models.CharField(max_length=50, unique=True, null=True, blank=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"Profile - {self.user.email}"


class EmailVerification(models.Model):
    """Email verification tokens (24-hour expiry)."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verifications')
    token = models.UUIDField(unique=True, default=uuid.uuid4)
    email = models.EmailField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email Verification'
        verbose_name_plural = 'Email Verifications'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"Verification - {self.email}"
    
    def is_expired(self):
        """Check if token has expired."""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if token is valid and not used."""
        return not self.is_used and not self.is_expired()
    
    @classmethod
    def create_for_user(cls, user):
        """Create a new verification token for user."""
        expires_at = timezone.now() + timedelta(hours=24)
        return cls.objects.create(
            user=user,
            email=user.email,
            expires_at=expires_at
        )


class PasswordReset(models.Model):
    """Password reset tokens (1-hour expiry)."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    token = models.UUIDField(unique=True, default=uuid.uuid4)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Password Reset'
        verbose_name_plural = 'Password Resets'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"Password Reset - {self.user.email}"
    
    def is_expired(self):
        """Check if token has expired."""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if token is valid and not used."""
        return not self.is_used and not self.is_expired()
    
    @classmethod
    def create_for_user(cls, user):
        """Create a new password reset token for user."""
        expires_at = timezone.now() + timedelta(hours=1)
        return cls.objects.create(
            user=user,
            expires_at=expires_at
        )


class OTPToken(models.Model):
    """OTP tokens for 2FA (10-minute expiry)."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_tokens')
    code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'OTP Token'
        verbose_name_plural = 'OTP Tokens'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['code']),
        ]
    
    def __str__(self):
        return f"OTP - {self.user.email}"
    
    def is_expired(self):
        """Check if OTP has expired."""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if OTP is valid and not used."""
        return not self.is_used and not self.is_expired()
    
    @classmethod
    def create_for_user(cls, user, code):
        """Create a new OTP token for user."""
        from django.conf import settings
        expires_at = timezone.now() + timedelta(seconds=settings.OTP_VALIDITY_DURATION)
        return cls.objects.create(
            user=user,
            code=code,
            expires_at=expires_at
        )
