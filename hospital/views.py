import csv
from django.http import HttpResponse
from django.db.models import Avg, Count
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Patient, Doctor, Appointment, UserProfile, Prescription, MedicalRecord, DoctorAvailability, Notification, Bill, Bed, Medicine, DoctorReview
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User

def dashboard(request):
    return render(request, 'hospital/dashboard.html')


@login_required(login_url='/login/')
def patients(request):
    try:
        role = request.user.userprofile.role
    except UserProfile.DoesNotExist:
        return redirect('/login/')
        
    if role == 'admin':
        data = Patient.objects.all()
    elif role == 'doctor':
        data = Patient.objects.filter(appointment__doctor__user=request.user).distinct()
    else:
        return redirect('/patient_dashboard')
        
    return render(request, 'hospital/patients.html', {'patients': data})

@login_required(login_url='/login/')
def doctors(request):
    data = Doctor.objects.annotate(
        avg_rating=Avg('doctorreview__rating'),
        review_count=Count('doctorreview')
    )
    return render(request, 'hospital/doctors.html', {'doctors': data})

@login_required(login_url='/login/')
def appointments(request):
    try:
        role = request.user.userprofile.role
    except UserProfile.DoesNotExist:
        return redirect('/login/')
        
    if role == 'admin':
        data = Appointment.objects.all()
    elif role == 'doctor':
        try:
            doctor = Doctor.objects.get(user=request.user)
            data = Appointment.objects.filter(doctor=doctor)
        except Doctor.DoesNotExist:
            # Fallback for manual data entry issues
            data = Appointment.objects.filter(doctor__name__icontains=request.user.username)
    elif role == 'patient':
        data = Appointment.objects.filter(patient__user=request.user)
    else:
        data = []
    
    return render(request, 'hospital/appointments.html', {'appointments': data})



@login_required(login_url='/login/')
def add_patient(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        return redirect('/')

    if request.method == "POST":
        name = request.POST['name']
        age = request.POST['age']
        gender = request.POST['gender']
        phone = request.POST['phone']
        address = request.POST['address']

        Patient.objects.create(
            name=name,
            age=age,
            gender=gender,
            phone=phone,
            address=address
        )

        return redirect('/patients')

    return render(request, 'hospital/add_patient.html')

@login_required(login_url='/login/')
def add_doctor(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        return redirect('/')

    if request.method == "POST":
        name = request.POST['name']
        specialization = request.POST['specialization']
        phone = request.POST['phone']
        email = request.POST['email']

        # Auto-create user account for doctor
        username = email.split('@')[0] + phone[-4:]
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(username=username, password='password123')
            UserProfile.objects.create(user=user, role='doctor')
        else:
            user = User.objects.get(username=username)

        Doctor.objects.create(
            user=user,
            name=name,
            specialization=specialization,
            phone=phone,
            email=email
        )

        return redirect('/doctors')

    return render(request, 'hospital/add_doctor.html')

@login_required(login_url='/login/')
def add_appointment(request):
    try:
        role = request.user.userprofile.role
    except UserProfile.DoesNotExist:
        return redirect('/login/')

    current_patient = None
    if role == 'patient':
        patients = Patient.objects.filter(user=request.user)
        current_patient = patients.first()
    else:
        patients = Patient.objects.all()

    doctors = Doctor.objects.all()

    if request.method == "POST":
        # Handle patient_id from either select or hidden input
        patient_id = request.POST.get('patient')
        if role == 'patient' and not patient_id and current_patient:
            patient_id = current_patient.id
            
        doctor_id = request.POST['doctor']
        date = request.POST['date']
        reason = request.POST['reason']

        # Security check for patients adding for someone else
        patient = Patient.objects.get(id=patient_id)
        if role == 'patient' and patient.user != request.user:
            return redirect('/appointments')

        selected_doctor = Doctor.objects.get(id=doctor_id)

        # Phase 2: Availability Validation (Check Day)
        import datetime
        booking_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        day_of_week = booking_date.weekday() # 0 is Monday
        
        is_available = DoctorAvailability.objects.filter(doctor=selected_doctor, day=day_of_week).exists()
        
        if not is_available:
            error = f"Dr. {selected_doctor.name} is not available on {booking_date.strftime('%A')}. Please choose another day."
            return render(request, 'hospital/add_appointment.html', {
                'patients': patients,
                'doctors': doctors,
                'current_patient': current_patient,
                'role': role,
                'error': error
            })

        Appointment.objects.create(
            patient=patient,
            doctor=selected_doctor,
            date=date,
            reason=reason
        )
        
        # Create Notification for Doctor
        Notification.objects.create(
            user=selected_doctor.user,
            message=f"New appointment request from {patient.name} for {date}."
        )

        return redirect('/appointments')

    return render(request, 'hospital/add_appointment.html', {
        'patients': patients,
        'doctors': doctors,
        'current_patient': current_patient,
        'role': role
    })

def user_login(request):
    error = None
    if request.method == "POST":

        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:

            login(request, user)

            try:
                profile = UserProfile.objects.get(user=user)

                if user.userprofile.role == 'admin':
                    return redirect('/admin_dashboard/')
                elif user.userprofile.role == 'doctor':
                    return redirect('/doctor_dashboard/')
                elif user.userprofile.role == 'patient':
                    return redirect('/patient_dashboard/')
                elif user.userprofile.role in ['nurse', 'pharmacist']:
                    return redirect('/staff_dashboard/')
                else:
                    return redirect('/')
            except UserProfile.DoesNotExist:
                error = "User profile role not properly configured."
        else:
            error = "Invalid username or password"

    return render(request,'hospital/login.html', {'error': error})

@login_required(login_url='/login/')
def admin_dashboard(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        return redirect('/')
    return render(request,'hospital/admin_dashboard.html')

@login_required(login_url='/login/')
def doctor_dashboard(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'doctor':
        return redirect('/')
    
    try:
        doctor = Doctor.objects.get(user=request.user)
        appointment_count = Appointment.objects.filter(doctor=doctor).count()
        patient_count = Patient.objects.filter(appointment__doctor=doctor).distinct().count()
        recent_appointments = Appointment.objects.filter(doctor=doctor).order_by('-date')[:5]
    except Doctor.DoesNotExist:
        # Fallback for manual data entry issues
        doctor_queryset = Doctor.objects.filter(name__icontains=request.user.username)
        if doctor_queryset.exists():
            doctor = doctor_queryset.first()
            # Repair the link automatically
            doctor.user = request.user
            doctor.save()
            appointment_count = Appointment.objects.filter(doctor=doctor).count()
            patient_count = Patient.objects.filter(appointment__doctor=doctor).distinct().count()
            recent_appointments = Appointment.objects.filter(doctor=doctor).order_by('-date')[:5]
        else:
            appointment_count = 0
            patient_count = 0
            recent_appointments = []
        
    return render(request,'hospital/doctor_dashboard.html', {
        'appointment_count': appointment_count,
        'patient_count': patient_count,
        'recent_appointments': recent_appointments
    })

@login_required(login_url='/login/')
def patient_dashboard(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'patient':
        return redirect('/')
    
    appointment_count = Appointment.objects.filter(patient__user=request.user).count()
    
    return render(request,'hospital/patient_dashboard.html', {
        'appointment_count': appointment_count
    })

@login_required(login_url='/login/')
def edit_patient(request, id):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        return redirect('/')
    patient = Patient.objects.get(id=id)
    if request.method == 'POST':
        patient.name = request.POST['name']
        patient.age = request.POST['age']
        patient.gender = request.POST['gender']
        patient.phone = request.POST['phone']
        patient.address = request.POST['address']
        patient.save()
        return redirect('/patients')
    return render(request, 'hospital/edit_patient.html', {'patient': patient})

@login_required(login_url='/login/')
def delete_patient(request, id):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        return redirect('/')
    patient = Patient.objects.get(id=id)
    if patient.user:
        patient.user.delete()
    patient.delete()
    return redirect('/patients')

@login_required(login_url='/login/')
def edit_doctor(request, id):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        return redirect('/')
    doctor = Doctor.objects.get(id=id)
    if request.method == 'POST':
        doctor.name = request.POST['name']
        doctor.specialization = request.POST['specialization']
        doctor.phone = request.POST['phone']
        doctor.email = request.POST['email']
        doctor.save()
        return redirect('/doctors')
    return render(request, 'hospital/edit_doctor.html', {'doctor': doctor})

@login_required(login_url='/login/')
def delete_doctor(request, id):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        return redirect('/')
    doctor = Doctor.objects.get(id=id)
    if doctor.user:
        doctor.user.delete()
    doctor.delete()
    return redirect('/doctors')

def patient_register(request):
    error = None
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        name = request.POST['name']
        age = request.POST['age']
        gender = request.POST['gender']
        phone = request.POST['phone']
        address = request.POST['address']

        # Check if username exists
        if User.objects.filter(username=username).exists():
            error = "Username already exists. Please choose a different one."
        else:
            # Create user
            user = User.objects.create_user(username=username, password=password)
            # Create profile
            UserProfile.objects.create(user=user, role='patient')
            # Create patient record
            Patient.objects.create(
                user=user,
                name=name,
                age=age,
                gender=gender,
                phone=phone,
                address=address
            )
            return redirect('/login/')
            
    return render(request, 'hospital/register.html', {'error': error})

def index(request):
    return render(request,'hospital/index.html')

@login_required(login_url='/login/')
def accept_appointment(request, id):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'doctor':
        return redirect('/')
    
    appointment = Appointment.objects.get(id=id)
    
    # Security: Ensure doctor can only accept their own appointment
    if appointment.doctor.user != request.user:
        return redirect('/appointments')

    if request.method == "POST":
        time = request.POST['time']
        appointment.appointment_time = time
        appointment.status = 'accepted'
        appointment.save()
        
        # Create Notification for Patient
        Notification.objects.create(
            user=appointment.patient.user,
            message=f"Your appointment with Dr. {appointment.doctor.name} on {appointment.date} has been ACCEPTED for {time}."
        )
        
        return redirect('/appointments')

    return render(request, 'hospital/accept_appointment.html', {'appointment': appointment})

@login_required(login_url='/login/')
def reject_appointment(request, id):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'doctor':
        return redirect('/')
    
    appointment = Appointment.objects.get(id=id)
    
    # Security check
    if appointment.doctor.user == request.user:
        appointment.status = 'rejected'
        appointment.save()
        
        # Create Notification for Patient
        Notification.objects.create(
            user=appointment.patient.user,
            message=f"Your appointment request for {appointment.date} with Dr. {appointment.doctor.name} was unfortunately rejected."
        )
    
    return redirect('/appointments')

@login_required(login_url='/login/')
def write_prescription(request, id):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'doctor':
        return redirect('/')
    
    appointment = Appointment.objects.get(id=id)
    if appointment.doctor.user != request.user:
        return redirect('/appointments')

    if request.method == "POST":
        details = request.POST['details']
        Prescription.objects.create(
            appointment=appointment,
            patient=appointment.patient,
            doctor=appointment.doctor,
            details=details
        )
        return redirect('/appointments/')

    return render(request, 'hospital/write_prescription.html', {'appointment': appointment})

@login_required(login_url='/login/')
def medical_records(request):
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return render(request, 'hospital/add_patient.html', {'error': 'Please complete your patient profile details first.'})

    records = MedicalRecord.objects.filter(patient=patient).order_by('-date_uploaded')
    
    if request.method == "POST":
        description = request.POST['description']
        file = request.FILES['file']
        MedicalRecord.objects.create(patient=patient, description=description, file=file)
        return redirect('/medical_records/')
        
    return render(request, 'hospital/medical_records.html', {'records': records})

@login_required(login_url='/login/')
def view_prescriptions(request):
    try:
        role = request.user.userprofile.role
    except UserProfile.DoesNotExist:
        return redirect('/login/')

    if role == 'patient':
        prescriptions = Prescription.objects.filter(patient__user=request.user).order_by('-date_created')
        return render(request, 'hospital/view_prescriptions.html', {'prescriptions': prescriptions})
    return redirect('/')

@login_required(login_url='/login/')
def set_availability(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'doctor':
        return redirect('/')
    
    doctor = Doctor.objects.get(user=request.user)
    availabilities = DoctorAvailability.objects.filter(doctor=doctor)
    
    if request.method == "POST":
        days = request.POST.getlist('days')
        # Clear existing and set new
        DoctorAvailability.objects.filter(doctor=doctor).delete()
        for day in days:
            DoctorAvailability.objects.create(doctor=doctor, day=int(day))
        return redirect('/doctor_dashboard/')
        
    return render(request, 'hospital/doctor_availability.html', {
        'availabilities': availabilities,
        'days_range': DoctorAvailability.DAY_CHOICES
    })

@login_required(login_url='/login/')
def notifications(request):
    notes = Notification.objects.filter(user=request.user).order_by('-created_at')
    # Mark all as read when viewed
    notes.update(is_read=True)
    return render(request, 'hospital/notifications.html', {'notifications': notes})

@login_required(login_url='/login/')
def generate_bill(request, appointment_id):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        return redirect('/')
    
    appointment = Appointment.objects.get(id=appointment_id)
    if request.method == "POST":
        amount = request.POST['amount']
        Bill.objects.create(
            patient=appointment.patient,
            appointment=appointment,
            amount=amount
        )
        # Update appointment status to completed when billed
        appointment.status = 'completed'
        appointment.save()
        return redirect('/bills_list/')
        
    return render(request, 'hospital/generate_bill.html', {'appointment': appointment})

@login_required(login_url='/login/')
def bills_list(request):
    try:
        role = request.user.userprofile.role
    except UserProfile.DoesNotExist:
        return redirect('/login/')

    if role == 'admin':
        bills = Bill.objects.all().order_by('-date_generated')
    elif role == 'patient':
        bills = Bill.objects.filter(patient__user=request.user).order_by('-date_generated')
    else:
        return redirect('/')
        
    return render(request, 'hospital/bills_list.html', {'bills': bills})

@login_required(login_url='/login/')
def manage_beds(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        return redirect('/')
    
    beds = Bed.objects.all().order_by('number')
    patients = Patient.objects.all()
    
    if request.method == "POST":
        # Check if we are adding a new bed or updating occupancy
        if 'add_bed' in request.POST:
            number = request.POST['number']
            Bed.objects.create(number=number)
        elif 'update_bed' in request.POST:
            bed_id = request.POST['bed_id']
            patient_id = request.POST.get('patient')
            bed = Bed.objects.get(id=bed_id)
            if patient_id:
                bed.patient = Patient.objects.get(id=patient_id)
                bed.is_occupied = True
            else:
                bed.patient = None
                bed.is_occupied = False
            bed.save()
        return redirect('/manage_beds/')
        
    return render(request, 'hospital/manage_beds.html', {'beds': beds, 'patients': patients})

@login_required(login_url='/login/')
def delete_bed(request, id):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        return redirect('/')
    Bed.objects.get(id=id).delete()
    return redirect('/manage_beds/')

@login_required(login_url='/login/')
def manage_pharmacy(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        return redirect('/')
    
    medicines = Medicine.objects.all().order_by('name')
    if request.method == "POST":
        if 'add_medicine' in request.POST:
            Medicine.objects.create(
                name=request.POST['name'],
                description=request.POST['description'],
                price=request.POST['price'],
                stock=request.POST['stock']
            )
        elif 'update_stock' in request.POST:
            med = Medicine.objects.get(id=request.POST['med_id'])
            med.stock = request.POST['stock']
            med.save()
        return redirect('/manage_pharmacy/')
        
    return render(request, 'hospital/manage_pharmacy.html', {'medicines': medicines})

@login_required(login_url='/login/')
def pharmacy_view(request):
    medicines = Medicine.objects.filter(is_available=True, stock__gt=0).order_by('name')
    return render(request, 'hospital/pharmacy_view.html', {'medicines': medicines})
@login_required(login_url='/login/')
def delete_bed(request, id):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        return redirect('/')
    try:
        Bed.objects.get(id=id).delete()
    except Bed.DoesNotExist:
        pass
    return redirect('/manage_beds/')

@login_required(login_url='/login/')
def export_patients_csv(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        return redirect('/')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="patients.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Name', 'Age', 'Gender', 'Phone', 'Address'])
    for patient in Patient.objects.all():
        writer.writerow([patient.id, patient.name, patient.age, patient.gender, patient.phone, patient.address])
    return response

@login_required(login_url='/login/')
def export_bills_csv(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        return redirect('/')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="bills.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Patient', 'Doctor', 'Amount', 'Date Generated', 'Status'])
    for bill in Bill.objects.all():
        status = 'Paid' if bill.is_paid else 'Unpaid'
        writer.writerow([bill.id, bill.patient.name, bill.appointment.doctor.name, bill.amount, bill.date_generated.strftime("%Y-%m-%d"), status])
    return response

@login_required(login_url='/login/')
def export_pharmacy_csv(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        return redirect('/')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="pharmacy_inventory.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Medicine Name', 'Price', 'Stock', 'Availability'])
    for med in Medicine.objects.all():
        avail = 'Available' if med.is_available else 'Unavailable'
        writer.writerow([med.id, med.name, med.price, med.stock, avail])
    return response

@login_required(login_url='/login/')
def rate_doctor(request, appointment_id):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'patient':
        return redirect('/')
    
    appointment = Appointment.objects.get(id=appointment_id)
    if appointment.patient.user != request.user or appointment.status != 'completed':
        return redirect('/appointments')
        
    if hasattr(appointment, 'doctorreview'):
        return redirect('/appointments') # Already reviewed
        
    if request.method == "POST":
        rating = int(request.POST['rating'])
        comment = request.POST['comment']
        DoctorReview.objects.create(
            appointment=appointment,
            patient=appointment.patient,
            doctor=appointment.doctor,
            rating=rating,
            comment=comment
        )
        return redirect('/appointments')
        
    return render(request, 'hospital/rate_doctor.html', {'appointment': appointment})
