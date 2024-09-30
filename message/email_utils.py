from django.core.mail import send_mail
from django.http import HttpResponse

def send_test_email(request):
    subject = 'Test Email'
    message = 'Hello'
    recipient_list = ['recipient@example.com']  # Replace with the actual recipient email address

    send_mail(
        subject,
        message,
        'mangazeen@gmail.com',  # This should be the email you're using as `DEFAULT_FROM_EMAIL`
        recipient_list,
        fail_silently=False,
    )

    return HttpResponse('Test email sent successfully!')
