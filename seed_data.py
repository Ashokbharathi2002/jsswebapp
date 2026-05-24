import os
import django
from datetime import datetime, timedelta

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solar_installation.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import SolarInstallationProject, Attendance

User = get_user_model()

def seed():
    print("Beginning database seeding...")
    
    # 1. Clear database of existing data (except Django contenttypes)
    SolarInstallationProject.objects.all().delete()
    Attendance.objects.all().delete()
    # Keep only the custom users
    User.objects.all().delete()

    # 2. Create Super User
    superuser = User.objects.create_superuser(
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
    print("Created Super User login: superuser / solar123")

    print("Database seeding completed successfully with clean Super User configuration!")

if __name__ == '__main__':
    seed()
