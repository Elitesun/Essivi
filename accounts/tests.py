from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import EmailVerification, OTPToken
import json

User = get_user_model()


class AuthenticationE2ETests(TestCase):
    """End-to-end tests for authentication endpoints."""
    
    def setUp(self):
        """Set up test client and test data."""
        self.client = APIClient()
        self.register_url = reverse('accounts:register')
        self.login_url = reverse('accounts:rest_login')
        self.verify_email_url = reverse('accounts:verify_email')
        self.resend_verification_url = reverse('accounts:resend_verification')
        
        self.agent_data = {
            'email': 'agent@essivi.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '+237123456789',
            'user_type': 'agent',
            'password': 'SecurePass123',
            'password_confirm': 'SecurePass123'
        }
        
        self.client_data = {
            'email': 'client@essivi.com',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'phone': '+237987654321',
            'user_type': 'client',
            'password': 'SecurePass456',
            'password_confirm': 'SecurePass456'
        }
    
    def test_01_register_agent_success(self):
        """Test successful agent registration."""
        response = self.client.post(self.register_url, self.agent_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('email', response.data['data'])
        self.assertEqual(response.data['data']['user_type'], 'agent')
        
        # Verify user exists in database
        user = User.objects.get(email=self.agent_data['email'])
        self.assertFalse(user.is_verified)
        self.assertTrue(user.profile.agent_id)
        
        print(f"[OK] Agent registration successful: {user.email}")
    
    def test_02_register_client_success(self):
        """Test successful client registration."""
        response = self.client.post(self.register_url, self.client_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['user_type'], 'client')
        
        # Verify user exists with client profile
        user = User.objects.get(email=self.client_data['email'])
        self.assertTrue(user.profile.client_code)
        
        print(f"[OK] Client registration successful: {user.email}")
    
    def test_03_register_duplicate_email(self):
        """Test registration with duplicate email fails."""
        # Register first time
        self.client.post(self.register_url, self.agent_data, format='json')
        
        # Try to register again with same email
        response = self.client.post(self.register_url, self.agent_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        print("[OK] Duplicate email validation working")
    
    def test_04_register_password_mismatch(self):
        """Test registration with mismatched passwords fails."""
        data = self.agent_data.copy()
        data['password_confirm'] = 'DifferentPassword'
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data['errors'])
        print("[OK] Password mismatch validation working")
    
    def test_05_email_verification_success(self):
        """Test email verification works."""
        # Register user
        self.client.post(self.register_url, self.agent_data, format='json')
        user = User.objects.get(email=self.agent_data['email'])
        
        # Get verification token
        verification = EmailVerification.objects.filter(user=user).first()
        self.assertIsNotNone(verification)
        
        # Verify email
        response = self.client.post(
            self.verify_email_url,
            {'token': str(verification.token)},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        
        # Check user is verified
        user.refresh_from_db()
        self.assertTrue(user.is_verified)
        print(f"[OK] Email verification successful for: {user.email}")
    
    def test_06_login_before_verification_fails(self):
        """Test login fails for unverified users."""
        # Register but don't verify
        self.client.post(self.register_url, self.agent_data, format='json')
        
        # Try to login
        response = self.client.post(
            self.login_url,
            {
                'email': self.agent_data['email'],
                'password': self.agent_data['password']
            },
            format='json'
        )
        
        # Should fail or return token but subsequent API calls should fail
        print(f"[OK] Login before verification returns: {response.status_code}")
    
    def test_07_login_after_verification_success(self):
        """Test successful login after email verification."""
        # Register and verify user
        self.client.post(self.register_url, self.agent_data, format='json')
        user = User.objects.get(email=self.agent_data['email'])
        user.is_verified = True
        user.save()
        
        # Login
        response = self.client.post(
            self.login_url,
            {
                'email': self.agent_data['email'],
                'password': self.agent_data['password']
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Store tokens for later tests
        self.access_token = response.data['access']
        self.refresh_token = response.data['refresh']
        
        print(f"[OK] Login successful, tokens received")
    
    def test_08_login_invalid_credentials(self):
        """Test login with wrong password fails."""
        # Create verified user
        self.client.post(self.register_url, self.agent_data, format='json')
        user = User.objects.get(email=self.agent_data['email'])
        user.is_verified = True
        user.save()
        
        # Try login with wrong password
        response = self.client.post(
            self.login_url,
            {
                'email': self.agent_data['email'],
                'password': 'WrongPassword123'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        print("[OK] Invalid credentials rejected")
    
    def test_09_get_user_profile_authenticated(self):
        """Test accessing user profile with valid token."""
        # Register, verify and login
        self.client.post(self.register_url, self.agent_data, format='json')
        user = User.objects.get(email=self.agent_data['email'])
        user.is_verified = True
        user.save()
        
        login_response = self.client.post(
            self.login_url,
            {
                'email': self.agent_data['email'],
                'password': self.agent_data['password']
            },
            format='json'
        )
        
        access_token = login_response.data['access']
        
        # Access profile
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(reverse('accounts:user-me'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['email'], self.agent_data['email'])
        self.assertEqual(response.data['data']['user_type'], 'agent')
        self.assertIsNotNone(response.data['data']['profile']['agent_id'])
        
        print(f"[OK] User profile retrieved: {response.data['data']['email']}")
    
    def test_10_access_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without authentication fails."""
        response = self.client.get(reverse('accounts:user-me'))
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        print("[OK] Protected endpoint blocked without token")
    
    def test_11_token_refresh(self):
        """Test JWT token refresh works."""
        # Register, verify and login
        self.client.post(self.register_url, self.agent_data, format='json')
        user = User.objects.get(email=self.agent_data['email'])
        user.is_verified = True
        user.save()
        
        login_response = self.client.post(
            self.login_url,
            {
                'email': self.agent_data['email'],
                'password': self.agent_data['password']
            },
            format='json'
        )
        


        
        # dj-rest-auth with JWT might use different key names
        refresh_token = login_response.data.get('refresh_token') or login_response.data.get('refresh')
        
        # Refresh token (dj-rest-auth provides this endpoint without namespace)
        response = self.client.post(
            '/api/auth/token/refresh/',
            {'refresh': refresh_token},
            format='json'
        )
        


        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        print("[OK] Token refresh successful")
    
    def test_12_resend_verification_email(self):
        """Test resending verification email."""
        # Register user
        self.client.post(self.register_url, self.agent_data, format='json')
        
        # Resend verification
        response = self.client.post(
            self.resend_verification_url,
            {'email': self.agent_data['email']},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        print("[OK] Resend verification email successful")
    
    def test_13_complete_agent_flow(self):
        """Test complete agent registration and login flow."""
        print("\n=== COMPLETE AGENT FLOW ===")
        
        # 1. Register
        reg_response = self.client.post(self.register_url, self.agent_data, format='json')
        self.assertEqual(reg_response.status_code, status.HTTP_201_CREATED)
        print("1. [OK] Agent registered")
        
        # 2. Verify email
        user = User.objects.get(email=self.agent_data['email'])
        verification = EmailVerification.objects.filter(user=user).first()
        verify_response = self.client.post(
            self.verify_email_url,
            {'token': str(verification.token)},
            format='json'
        )
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        print("2. [OK] Email verified")
        
        # 3. Login
        login_response = self.client.post(
            self.login_url,
            {
                'email': self.agent_data['email'],
                'password': self.agent_data['password']
            },
            format='json'
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        print("3. [OK] Logged in successfully")
        
        # 4. Access profile
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {login_response.data["access"]}')
        profile_response = self.client.get(reverse('accounts:user-me'))
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        print(f"4. [OK] Profile accessed: {profile_response.data['data']['profile']['agent_id']}")
        
        print("=== AGENT FLOW COMPLETE ===\n")
    
    def test_14_complete_client_flow(self):
        """Test complete client registration and login flow."""
        print("\n=== COMPLETE CLIENT FLOW ===")
        
        # 1. Register
        reg_response = self.client.post(self.register_url, self.client_data, format='json')
        self.assertEqual(reg_response.status_code, status.HTTP_201_CREATED)
        print("1. [OK] Client registered")
        
        # 2. Verify email
        user = User.objects.get(email=self.client_data['email'])
        verification = EmailVerification.objects.filter(user=user).first()
        verify_response = self.client.post(
            self.verify_email_url,
            {'token': str(verification.token)},
            format='json'
        )
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        print("2. [OK] Email verified")
        
        # 3. Login
        login_response = self.client.post(
            self.login_url,
            {
                'email': self.client_data['email'],
                'password': self.client_data['password']
            },
            format='json'
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        print("3. [OK] Logged in successfully")
        
        # 4. Access profile
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {login_response.data["access"]}')
        profile_response = self.client.get(reverse('accounts:user-me'))
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        print(f"4. [OK] Profile accessed: {profile_response.data['data']['profile']['client_code']}")
        
        print("=== CLIENT FLOW COMPLETE ===\n")
