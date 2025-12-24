from django.db import models
from django.contrib.auth.models import User

class TestRecord(models.Model):
    # Link to the User Account
    patient = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    date_of_test = models.DateField(help_text="Date sample was collected")
    
    # --- VERIFICATION FIELDS ---
    aadhaar_number = models.CharField(max_length=12, default='000000000000', help_text="12-digit Aadhaar Number")
    phone_number = models.CharField(max_length=15, default='0000000000', help_text="Patient Phone Number for OTP")
    
    # This checks if the user finished the OTP step
    is_verified = models.BooleanField(default=False) 

    # --- MEDICAL DATA ---
    SYMPTOM_CHOICES = [
        ('Cough', 'Cough'),
        ('Fever', 'Fever'),
        ('Wheezing', 'Wheezing'),
        ('Shortness of Breath', 'Shortness of Breath'),
        ('Sore Throat', 'Sore Throat'),
        ('Runny Nose', 'Runny Nose'),
        ('Other', 'Other'),
    ]
    symptoms = models.CharField(max_length=100, choices=SYMPTOM_CHOICES, default='Cough')
    
    TEST_TYPE_CHOICES = [
        ('PCR', 'RT-PCR (Polymerase Chain Reaction)'),
        ('Antigen', 'Antigen Rapid Test'),
        ('Culture', 'Viral Culture'),
        ('Serology', 'Serology (Blood Test)'),
    ]
    test_type = models.CharField(max_length=50, choices=TEST_TYPE_CHOICES, default='PCR')

    # --- RESULT & PROOF ---
    # The result (Admin sets this later to Positive/Negative)
    test_result = models.CharField(max_length=20, default='Pending')
    
    # Uploaded ID Proof (Aadhaar Photo)
    report_image = models.ImageField(upload_to='reports/', blank=True, null=True, help_text="Upload ID Proof or Doctor's Referral")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "Verified" if self.is_verified else "Unverified"
        return f"{self.patient.username} - {self.test_result} ({status})"

class VaccinationRecord(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    date_of_vaccination = models.DateField()
    
    VACCINE_CHOICES = [
        ('Toxoid', 'Toxoid'),
        ('Polysaccharide', 'Polysaccharide'),
        ('mRNA', 'mRNA'),
        ('Other', 'Other'),
    ]
    vaccine_type = models.CharField(max_length=50, choices=VACCINE_CHOICES, default='Toxoid')
    
    certificate_image = models.ImageField(upload_to='certificates/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.patient.username} - {self.vaccine_type}"