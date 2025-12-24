from django.contrib import admin
from .models import TestRecord, VaccinationRecord
from django.core.mail import EmailMessage
from django.conf import settings

@admin.register(TestRecord)
class TestRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'date_of_test', 'test_result', 'created_at')
    list_filter = ('test_result',)
    search_fields = ('patient__username', 'patient__email')

    # This function runs every time you click "SAVE" in the admin panel
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        # Check if the result is NO LONGER "Pending" (meaning Admin updated it)
        if obj.test_result != 'Pending' and obj.patient.email:
            subject = f'HMPV Test Result Update: {obj.test_result}'
            message = f"""
            Dear {obj.patient.username},

            Your HMPV test result from {obj.date_of_test} has been updated.

            Result: {obj.test_result}

            Please login to the portal for more details.
            """
            
            email = EmailMessage(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [obj.patient.email]
            )
            email.send(fail_silently=True)

@admin.register(VaccinationRecord)
class VaccinationRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'vaccine_type', 'date_of_vaccination')
    search_fields = ('patient__username', 'patient__email')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # If Admin uploads a certificate, email it to the patient
        if obj.certificate_image and obj.patient.email:
            subject = 'HMPV Vaccination Certificate Uploaded'
            message = f"""
            Dear {obj.patient.username},

            Your vaccination record for {obj.vaccine_type} has been updated.
            We have attached your certificate to this email.
            """
            
            email = EmailMessage(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [obj.patient.email]
            )
            
            # Attach the file (The certificate image)
            email.attach_file(obj.certificate_image.path)
            
            email.send(fail_silently=True)