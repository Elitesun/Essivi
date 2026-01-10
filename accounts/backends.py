from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that authenticates users by email
    instead of username.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user by email instead of username.
        The 'username' parameter is actually the email.
        """
        if not username or not password:
            return None
            
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def get_user(self, user_id):
        """Get user by ID (UUID in this case)."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
