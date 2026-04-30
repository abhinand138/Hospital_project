import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_project.settings')
django.setup()

from django.contrib.auth.models import User
from hospital.models import Patient, UserProfile

try:
    u = User.objects.get(username='arun')
    print(f"User 'arun' found. User ID: {u.id}")
    
    # Check UserProfile
    profile, created = UserProfile.objects.get_or_create(user=u, defaults={'role': 'patient'})
    if created:
        print("Created UserProfile for arun as 'patient'")
    else:
        print(f"UserProfile exists. Role: {profile.role}")
        if profile.role != 'patient':
            profile.role = 'patient'
            profile.save()
            print("Updated UserProfile role to 'patient'")
            
    # Check Patient model
    patient_exists = Patient.objects.filter(user=u).exists()
    if not patient_exists:
        Patient.objects.create(
            user=u,
            name='Arun',
            age=25,
            gender='Male',
            phone='0000000000',
            address='Placeholder Address'
        )
        print("Successfully created Patient record for 'arun'")
    else:
        print("Patient record already exists for 'arun'")

except User.DoesNotExist:
    print("User 'arun' not found. Skip repair.")
except Exception as e:
    print(f"Error during repair: {e}")
