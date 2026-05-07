"""hospital_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from hospital import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.index),

    path('login/', views.user_login),
    path('register/', views.patient_register),
    path('admin_dashboard/', views.admin_dashboard),
    path('doctor_dashboard/', views.doctor_dashboard),
    path('patient_dashboard/', views.patient_dashboard),

    path('patients/', views.patients),
    path('doctors/', views.doctors),
    path('appointments/', views.appointments),
    path('add_patient/', views.add_patient),
    path('edit_patient/<int:id>/', views.edit_patient),
    path('delete_patient/<int:id>/', views.delete_patient),
    path('add_doctor/', views.add_doctor),
    path('edit_doctor/<int:id>/', views.edit_doctor),
    path('delete_doctor/<int:id>/', views.delete_doctor),
    path('add_appointment/', views.add_appointment),
    path('accept_appointment/<int:id>/', views.accept_appointment),
    path('reject_appointment/<int:id>/', views.reject_appointment),
    path('write_prescription/<int:id>/', views.write_prescription),
    path('medical_records/', views.medical_records),
    path('view_prescriptions/', views.view_prescriptions),
    path('set_availability/', views.set_availability),
    path('notifications/', views.notifications),
    path('generate_bill/<int:appointment_id>/', views.generate_bill),
    path('bills_list/', views.bills_list),
    path('manage_beds/', views.manage_beds),
    path('delete_bed/<int:id>/', views.delete_bed),
    
    
    path('manage_pharmacy/', views.manage_pharmacy),
    path('pharmacy_view/', views.pharmacy_view),
    path('export_patients/', views.export_patients_csv),
    path('export_bills/', views.export_bills_csv),
    path('export_pharmacy/', views.export_pharmacy_csv),
    path('rate_doctor/<int:appointment_id>/', views.rate_doctor),
    path('buy_medicine/<int:id>/', views.buy_medicine),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)