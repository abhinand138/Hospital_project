import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_project.settings')
django.setup()

from hospital.models import Doctor, UserProfile
from django.contrib.auth.models import User

# Fix for Dr Manoj
try:
    manoj_user = User.objects.get(username='manoj')
    manoj_doctor = Doctor.objects.get(name='Dr Manoj')
    
    if manoj_doctor.user is None:
        manoj_doctor.user = manoj_user
        manoj_doctor.save()
        print("Successfully linked Dr Manoj to user 'manoj'")
    else:
        print("Dr Manoj was already linked.")
except Exception as e:
    print(f"Error during link repair: {e}")

# General check for other doctors
for doctor in Doctor.objects.filter(user=None):
    # Try to find a user with a similar name
    clean_name = doctor.name.replace('Dr ', '').replace('Dr. ', '').strip().lower()
    user = User.objects.filter(username__icontains=clean_name).first()
    if user:
        doctor.user = user
        doctor.save()
        print(f"Auto-linked {doctor.name} to user {user.username}")
