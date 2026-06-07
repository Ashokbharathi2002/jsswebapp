from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import LoginLog

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    if request is not None:
        # Retrieve IP address, checking proxy headers first
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Retrieve browser/device User Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Save to logs table
        LoginLog.objects.create(
            user=user,
            ip_address=ip,
            user_agent=user_agent
        )
    else:
        # Handle cases where request object is not provided (e.g. unit tests / management commands)
        LoginLog.objects.create(
            user=user,
            ip_address=None,
            user_agent=None
        )
