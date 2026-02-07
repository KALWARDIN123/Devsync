import os
import django
from django.core.mail import send_mail
from django.conf import settings

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'devsync.settings')
django.setup()

def test_email_config():
    print("Current email settings:")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    try:
        send_mail(
            subject='Test Email from DevSync',
            message='This is a test email to verify the SMTP configuration.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['cassassink@gmail.com'],
            fail_silently=False,
        )
        print("\nEmail sent successfully!")
    except Exception as e:
        print("\nError sending email:")
        print(str(e))

if __name__ == '__main__':
    test_email_config() 