# 🔐 **ACCOUNTS & AUTHENTICATION SYSTEM**

## 📋 **Quick Reference**
- **Auth Method**: Email-based (NO SMS)
- **User Types**: Agent, Client, Admin (3 only)
- **2FA**: Email OTP only
- **Framework**: Django REST + JWT (`djangorestframework-simplejwt`)
- **Database**: PostgreSQL

---

## 🗄️ **CORE MODELS**

### **User Model** (AbstractBaseUser)
```python
class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = (
        ('agent', 'Agent Commercial'),
        ('client', 'Client/Point de Vente'),
        ('admin', 'Administrator'),
    )
    
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    email = EmailField(unique=True, db_index=True)
    phone = CharField(max_length=20, blank=True, null=True)
    user_type = CharField(max_length=20, choices=USER_TYPE_CHOICES)
    first_name = CharField(max_length=100)
    last_name = CharField(max_length=100)
    
    # Status
    is_active = BooleanField(default=True)
    is_verified = BooleanField(default=False)  # Email verified
    is_staff = BooleanField(default=False)
    is_superuser = BooleanField(default=False)
    
    # Timestamps
    date_joined = DateTimeField(auto_now_add=True)
    last_login = DateTimeField(auto_now=True)
    
    # 2FA
    two_factor_enabled = BooleanField(default=False)
    two_factor_secret = CharField(max_length=32, blank=True)  # Email OTP seed
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['user_type', 'first_name', 'last_name']
```

### **UserProfile Model**
```python
class UserProfile(models.Model):
    user = OneToOneField(User, on_delete=CASCADE, related_name='profile')
    profile_picture = ImageField(upload_to='profiles/', null=True, blank=True)
    address = TextField(blank=True)
    city = CharField(max_length=100, blank=True)
    
    # Agent fields
    agent_id = CharField(max_length=50, unique=True, null=True, blank=True)
    tricycle_plate = CharField(max_length=50, blank=True)
    hire_date = DateField(null=True, blank=True)
    
    # Client fields
    business_name = CharField(max_length=200, blank=True)
    contact_person = CharField(max_length=200, blank=True)
    client_code = CharField(max_length=50, unique=True, null=True, blank=True)
    
    # GPS
    latitude = DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

### **EmailVerification Model**
```python
class EmailVerification(models.Model):
    user = ForeignKey(User, on_delete=CASCADE, related_name='email_verifications')
    token = UUIDField(default=uuid.uuid4, unique=True)
    email = EmailField()
    is_used = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    expires_at = DateTimeField()  # 24 hours from creation
```

### **PasswordReset Model**
```python
class PasswordReset(models.Model):
    user = ForeignKey(User, on_delete=CASCADE, related_name='password_resets')
    token = UUIDField(default=uuid.uuid4, unique=True)
    is_used = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    expires_at = DateTimeField()  # 1 hour from creation
```

---

## 📦 **SERIALIZERS**

| Serializer | Purpose |
|-----------|---------|
| `UserRegistrationSerializer` | POST register with email/password/user_type |
| `UserLoginSerializer` | POST login with email/password |
| `UserProfileSerializer` | GET/PUT user profile + agent/client specific fields |
| `EmailVerificationSerializer` | POST request email verification |
| `PasswordResetRequestSerializer` | POST request password reset |
| `PasswordResetConfirmSerializer` | POST confirm reset with token + new password |
| `ChangePasswordSerializer` | POST change password (current + new) |

---

## 🎮 **ENDPOINTS** (All under `/api/auth/`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `register/` | Register new user → sends verification email |
| POST | `verify-email/` | Verify email with token |
| POST | `resend-verification/` | Resend verification email |
| POST | `login/` | Login with email/password → returns JWT tokens |
| POST | `logout/` | Logout → blacklist refresh token |
| POST | `token/refresh/` | Refresh access token |
| POST | `password-reset/` | Request password reset → sends email |
| POST | `password-reset/confirm/` | Confirm reset with token + new password |
| POST | `change-password/` | Change password (authenticated) |
| GET/PUT | `profile/` | Get/update user profile |
| POST | `2fa/send-otp/` | Send email OTP (optional) |
| POST | `2fa/verify-otp/` | Verify email OTP |

---

## 🔑 **JWT TOKEN RESPONSE**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user_type": "agent",
  "email": "user@example.com",
  "is_verified": true
}
```

**Token Lifetimes:**
- Access: 60 minutes
- Refresh: 7 days
- Refresh rotation: enabled (new token on each refresh)

---

## 🛡️ **PERMISSIONS**

```python
class IsVerifiedUser(permissions.BasePermission):
    """User must be authenticated AND email verified"""
    
class IsAdminUser(permissions.BasePermission):
    """User must be admin (user_type='admin')"""
    
class IsAgentUser(permissions.BasePermission):
    """User must be agent (user_type='agent')"""
    
class IsClientUser(permissions.BasePermission):
    """User must be client (user_type='client')"""
```

---

## 📧 **EMAIL TEMPLATES NEEDED**

1. **Verification Email** → link to `/verify-email/{token}/`
2. **Password Reset Email** → link to `/reset-password/{token}/`
3. **Login Notification** → confirmation of login
4. **2FA OTP Email** → 6-digit code valid 10 minutes

---

## ⚙️ **SETTINGS CONFIGURATION**

```python
# settings.py
AUTH_USER_MODEL = 'accounts.User'
AUTHENTICATION_BACKENDS = ['accounts.backends.EmailBackend']

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = 'ESSIVI <noreply@essivi.com>'

# File uploads
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')
```

---

## 🚀 **IMPLEMENTATION CHECKLIST**

### Phase 1: Setup
- [ ] Install packages: `djangorestframework`, `djangorestframework-simplejwt`, `django-cors-headers`, `Pillow`
- [ ] Configure PostgreSQL in settings
- [ ] Set `AUTH_USER_MODEL` and JWT settings

### Phase 2: Models
- [ ] Create Custom User model
- [ ] Create UserProfile model
- [ ] Create EmailVerification model
- [ ] Create PasswordReset model
- [ ] Run migrations

### Phase 3: Auth Endpoints
- [ ] Registration (with email verification)
- [ ] Email verification
- [ ] Login (with JWT tokens)
- [ ] Logout
- [ ] Token refresh

### Phase 4: Account Management
- [ ] Password reset request
- [ ] Password reset confirm
- [ ] Change password
- [ ] Profile CRUD

### Phase 5: Advanced (Optional)
- [ ] Email-based 2FA (OTP)
- [ ] Rate limiting on auth endpoints
- [ ] Login history tracking

---

## 🔍 **CRITICAL RULES**

1. **Email Verification Required**: Users cannot login until email is verified
2. **No Password Storage**: Never log or display passwords
3. **Token Blacklisting**: On logout, refresh token goes to blacklist
4. **Rate Limiting**: 
   - Login: 5 attempts per 15 minutes
   - Registration: 3 per hour per IP
   - Password reset: 3 per day per email
5. **Session Timeout**: Auto-logout after 30 minutes of inactivity (frontend enforced)
6. **Agent/Client Auto-Setup**: When user registers with type='agent', create corresponding Agent record via signal

---

## 📌 **NOTES FOR AI AGENT**

- Always verify `is_verified=True` before allowing API access (except for auth endpoints)
- Use `user.user_type` to determine permissions, not `is_staff`/`is_superuser`
- Send emails asynchronously (use Celery or task queue in production)
- Implement CORS only for trusted domains (mobile apps + Next.js admin)
- Use `django.db.models.signals` post_save to auto-create UserProfile
- Email verification tokens: valid 24 hours
- Password reset tokens: valid 1 hour
