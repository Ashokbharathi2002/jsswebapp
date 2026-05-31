import os
import django

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solar_installation.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

def create_superuser_safely():
    if not User.objects.filter(username="superuser").exists():
        User.objects.create_superuser(
            username="superuser",
            email="superuser@solar.com",
            password="solar123",
            role="SUPERUSER",
            is_approved=True,
            first_name="Root",
            last_name="Admin",
            bio="Root System Administrator.",
            phone_number="+919999999999",
            whatsapp_number="919999999999"
        )
        print("Default superuser created: superuser / solar123")
    else:
        print("Superuser 'superuser' already exists. Skipping creation.")

if __name__ == '__main__':
    create_superuser_safely()
