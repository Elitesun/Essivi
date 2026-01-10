from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserProfile, EmailVerification
import string
import random


def generate_agent_id():
    """Generate unique agent ID in format: AGENT-XXXXXX"""
    return f"AGENT-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"


def generate_client_code():
    """Generate unique client code in format: CLIENT-XXXXXX"""
    return f"CLIENT-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to create a UserProfile when a User is created.
    Auto-generates agent_id or client_code based on user_type.
    """
    if created:
        profile_data = {}
        
        if instance.user_type == 'agent':
            profile_data['agent_id'] = generate_agent_id()
        elif instance.user_type == 'client':
            profile_data['client_code'] = generate_client_code()
        
        UserProfile.objects.create(user=instance, **profile_data)


@receiver(post_save, sender=User)
def create_email_verification(sender, instance, created, **kwargs):
    """
    Signal to create an EmailVerification token when a User is created.
    """
    if created and not instance.is_verified:
        EmailVerification.create_for_user(instance)
