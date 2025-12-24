import random
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from .models import TestRecord, VaccinationRecord
from .forms import UserRegisterForm
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from twilio.rest import Client
from .utils import send_whatsapp_message
from django.contrib.admin.views.decorators import staff_member_required
from .utils import generate_and_send_certificate

# 1. Registration View
def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Send Welcome Email
            subject = 'Welcome to HMPV Portal'
            message = f'Hi {user.username},\n\nThank you for registering.'
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [user.email]
            send_mail(subject, message, email_from, recipient_list, fail_silently=True)

            login(request, user)
            return redirect('index')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})

# 2. Login View
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # --- NEW LOGIC: SEPARATE ADMIN AND USER ---
            if user.is_staff or user.is_superuser:
                return redirect('admin_dashboard')  # Admin goes to Approval Page
            else:
                return redirect('index')  # Patient goes to Form Page
            # ------------------------------------------
            
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

# 3. Logout View
def logout_view(request):
    logout(request)
    return redirect('login')

# 4. Info Page
def info_view(request):
    return render(request, 'info.html')

# 5. Main Dashboard (STEP 1: Submit Data)
@login_required
def index(request):
    if request.method == "POST" and 'submit_test' in request.POST:
        # 1. Get Form Data
        date = request.POST.get('testDate')
        symp = request.POST.get('symptoms')
        t_type = request.POST.get('testType')
        aadhaar = request.POST.get('aadhaarNumber')
        phone = request.POST.get('phoneNumber')
        image = request.FILES.get('reportImage')
        
        # 2. Save "Unverified" Record
        record = TestRecord.objects.create(
            patient=request.user, 
            date_of_test=date, 
            symptoms=symp,
            test_type=t_type,
            aadhaar_number=aadhaar,
            phone_number=phone,
            report_image=image,
            test_result="Pending",
            is_verified=False 
        )
        
        # 3. Generate 4-digit OTP
        otp = str(random.randint(1000, 9999))
        
        # 4. Save to Session
        request.session['verification_otp'] = otp
        request.session['pending_record_id'] = record.id
        
        # 5. SEND WHATSAPP (Using your new utils.py!)
        try:
            # Check for country code (Default to India)
            if not phone.startswith('+'):
                phone = '+91' + phone
                
            msg_body = f"Your HMPV Verification Code is: {otp}"
            
            # This calls the function inside utils.py
            send_whatsapp_message(phone, msg_body)
            print("WhatsApp OTP sent successfully via utils.")
            
        except Exception as e:
            print(f"Error sending WhatsApp: {e}")

        # 6. Redirect to Verification Page
        return redirect('verify_otp_page')

    # ... (Keep vaccination logic and context the same) ...
    # (Copy the rest from your previous file)
    if request.method == "POST" and 'submit_vaccine' in request.POST:
        date = request.POST.get('vaccineDate')
        v_type = request.POST.get('vaccineType')
        image = request.FILES.get('certImage')
        VaccinationRecord.objects.create(patient=request.user, date_of_vaccination=date, vaccine_type=v_type, certificate_image=image)
        return redirect('index')

    latest_test = TestRecord.objects.filter(patient=request.user, is_verified=True).order_by('-created_at').first()
    latest_vaccine = VaccinationRecord.objects.filter(patient=request.user).order_by('-created_at').first()

    context = { 'latest_test': latest_test, 'latest_vaccine': latest_vaccine, 'user': request.user }
    return render(request, 'index.html', context)

# 6. OTP Verification Page (STEP 2: Verify Code)
@login_required
def verify_otp_page(request):
    if request.method == 'POST':
        user_entered_otp = request.POST.get('otpInput')
        system_otp = request.session.get('verification_otp')
        record_id = request.session.get('pending_record_id')
        
        if user_entered_otp and user_entered_otp == system_otp and record_id:
            # Verified!
            record = get_object_or_404(TestRecord, id=record_id)
            record.is_verified = True
            record.save()
            
            # Cleanup
            del request.session['verification_otp']
            del request.session['pending_record_id']
            
            return render(request, 'success.html')
        else:
            return render(request, 'otp_verify.html', {'error': 'Invalid OTP. Please check your phone messages.'})

    return render(request, 'otp_verify.html')

def send_test_whatsapp(request):
    phone = "+91XXXXXXXXXX"  # your WhatsApp number
    message = "Hello 👋 This message is sent from Django via Twilio WhatsApp!"

    sid = send_whatsapp_message(phone, message)
    return JsonResponse({"status": "sent", "sid": sid})


# tracker/views.py

@staff_member_required
def admin_dashboard(request):
    # Get Pending Tests
    pending_tests = TestRecord.objects.filter(test_result="Pending").order_by('-date_of_test')
    
    # --- NEW: Get Pending Vaccinations ---
    pending_vaccines = VaccinationRecord.objects.filter(is_verified=False).order_by('-date_of_vaccination')
    
    context = {
        'pending_tests': pending_tests,
        'pending_vaccines': pending_vaccines # Pass this to the HTML
    }
    return render(request, 'admin_dashboard.html', context)

# 8. APPROVE ACTION (Triggered by button click)
@staff_member_required
def approve_test_action(request, record_id, result):
    # 1. Get the record
    record = get_object_or_404(TestRecord, id=record_id)
    
    # 2. Update Result
    record.test_result = result  # "Positive" or "Negative"
    record.save()
    
    # 3. Generate Certificate & Email
    try:
        generate_and_send_certificate(record)
        print(f"Certificate sent to {record.patient.email}")
    except Exception as e:
        print(f"Error sending email: {e}")
        
    return redirect('admin_dashboard')

def admin_login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # --- SECURITY CHECK ---
            if user.is_staff or user.is_superuser:
                # User IS an Admin -> Let them in
                login(request, user)
                return redirect('admin_dashboard')
            else:
                # User is valid, BUT NOT AN ADMIN -> Block them
                return render(request, 'admin_login.html', {
                    'form': form, 
                    'error': 'ACCESS DENIED: You do not have Admin privileges.'
                })
    else:
        form = AuthenticationForm()
        
    return render(request, 'admin_login.html', {'form': form})


@staff_member_required
def approve_vaccine(request, record_id):
    # Get the specific vaccination record
    vaccine = get_object_or_404(VaccinationRecord, id=record_id)
    
    # Mark it as verified
    vaccine.is_verified = True
    vaccine.save()
    
    # Refresh the dashboard
    return redirect('admin_dashboard')