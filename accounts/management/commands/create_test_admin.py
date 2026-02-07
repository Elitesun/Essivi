from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Creates a test admin user for development'

    def handle(self, *args, **options):
        User = get_user_model()
        from accounts.models import AdminUser
        
        email = 'admin@essivivi.com'
        password = 'password123'

        if not User.objects.filter(email=email).exists():
            user = User.objects.create_superuser(
                email=email,
                password=password,
                first_name='Admin',
                last_name='Test',
                is_verified=True
            )
            
            # Create AdminUser profile
            AdminUser.objects.create(
                user=user,
                name='Admin Test',
                role='super_admin',
                status='actif'
            )
            
