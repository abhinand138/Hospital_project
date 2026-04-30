import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_project.settings')
django.setup()

from hospital.models import Doctor, Appointment, UserProfile, Patient
from django.contrib.auth.models import User

print("--- Data Audit ---")
print(f"Users: {User.objects.count()}")
print(f"UserProfiles: {UserProfile.objects.count()}")
print(f"Doctors: {Doctor.objects.count()}")
print(f"Patients: {Patient.objects.count()}")
print(f"Appointments: {Appointment.objects.count()}")

print("\n--- Doctors Audit ---")
for d in Doctor.objects.all():
    print(f"Doctor: {d.name}, Linked User: {d.user.username if d.user else 'None'}")

print("\n--- Appointments Audit ---")
for a in Appointment.objects.all():
    print(f"App: {a.patient.name} with Dr. {a.doctor.name} on {a.date}")

print("\n--- User Audit ---")
for u in User.objects.all():
    try:
        role = u.userprofile.role
    except:
        role = "No Profile"
    print(f"User: {u.username}, Role: {role}")
