from django.contrib import admin
from .models import Patient, Doctor, Appointment
from .models import UserProfile

admin.site.register(Patient)
admin.site.register(Doctor)
admin.site.register(Appointment)
admin.site.register(UserProfile)
