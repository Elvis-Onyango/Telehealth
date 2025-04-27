from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_appointment_reminder(email, appointment_date):
    send_mail(
        'Appointment Reminder',
        f'You have an appointment scheduled for {appointment_date}.',
        'noreply@telemed.com',
        [email],
        fail_silently=False,
    )
