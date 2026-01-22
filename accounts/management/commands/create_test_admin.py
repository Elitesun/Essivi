from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Creates a test admin user for development'

    def handle(self, *args, **options):
        User = get_user_model()
        email = 'admin@essivivi.com'
        password = 'password123'

        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(
                email=email,
                password=password,
                first_name='Admin',
                last_name='Test',
                is_verified=True
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully created admin user: {email} / {password}'))
        else:
            self.stdout.write(self.style.WARNING(f'Admin user {email} already exists'))
