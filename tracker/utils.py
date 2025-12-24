from twilio.rest import Client
from django.conf import settings
import os
from django.conf import settings
from django.core.mail import EmailMessage
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors

def send_whatsapp_message(to, message):
    client = Client(
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN
    )

    msg = client.messages.create(
        from_=settings.TWILIO_WHATSAPP_NUMBER,
        to=f"whatsapp:{to}",
        body=message
    )

    return msg.sid

def generate_and_send_certificate(test_record):
    """
    Generates a PDF Certificate and emails it to the patient.
    """
    # 1. Define File Path
    filename = f"HMPV_Certificate_{test_record.aadhaar_number}.pdf"
    file_path = os.path.join(settings.MEDIA_ROOT, 'certificates', filename)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # 2. Create PDF (Landscape Mode)
    c = canvas.Canvas(file_path, pagesize=landscape(letter))
    width, height = landscape(letter)

    # --- DESIGN ---
    # Border
    c.setStrokeColor(colors.darkblue)
    c.setLineWidth(5)
    c.rect(30, 30, width-60, height-60)
    
    # Header
    c.setFont("Helvetica-Bold", 30)
    c.setFillColor(colors.darkblue)
    c.drawCentredString(width/2, height - 100, "HMPV TEST CERTIFICATE")
    
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)
    c.drawCentredString(width/2, height - 130, "Official Medical Report - Strictly Confidential")

    # Content
    c.setFont("Helvetica", 18)
    text_y = height - 200
    
    c.drawString(100, text_y, f"Patient Name: {test_record.patient.username}")
    c.drawString(100, text_y - 40, f"Aadhaar Number: {test_record.aadhaar_number}")
    c.drawString(100, text_y - 80, f"Phone Number: {test_record.phone_number}")
    c.drawString(100, text_y - 120, f"Date of Sample: {test_record.date_of_test}")
    
    # Result (Big and Bold)
    c.setFont("Helvetica-Bold", 24)
    if test_record.test_result == "Negative":
        c.setFillColor(colors.green)
    else:
        c.setFillColor(colors.red)
        
    c.drawString(100, text_y - 180, f"TEST RESULT: {test_record.test_result.upper()}")

    # Footer
    c.setFont("Helvetica-Oblique", 10)
    c.setFillColor(colors.gray)
    c.drawCentredString(width/2, 50, "This is a computer-generated report. No signature required.")
    
    c.save()

    # 3. Email the PDF
    subject = f"Your HMPV Test Certificate - {test_record.test_result}"
    body = f"Dear {test_record.patient.username},\n\nYour test result has been processed by our Admin. Please find your official certificate attached.\n\nResult: {test_record.test_result}\n\nStay Safe,\nHMPV Admin Team"
    
    email = EmailMessage(
        subject,
        body,
        settings.EMAIL_HOST_USER,
        [test_record.patient.email],
    )
    email.attach_file(file_path)
    email.send(fail_silently=False)
    
    return file_path
