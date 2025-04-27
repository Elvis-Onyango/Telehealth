from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps  # Import apps to dynamically get the model
from config.utils import send_sms

@receiver(post_save, sender=None)  # Remove direct reference to Appointment
def send_appointment_notification(sender, instance, created, **kwargs):
    """
    Sends SMS notifications when an appointment is booked, confirmed, or cancelled.
    """
    Appointment = apps.get_model('appointments', 'Appointment')  # Lazy load model

    if isinstance(instance, Appointment):
        patient_number = instance.patient.phone
        doctor_number = instance.doctor.user.phone

        if created:
            message = f"Hello {instance.patient.get_full_name()}, your appointment with Dr. {instance.doctor.user.get_full_name()} is scheduled for {instance.date} at {instance.time}. Thank you!"
            send_sms(patient_number, message)
            send_sms(doctor_number, f"New appointment with {instance.patient.get_full_name()} on {instance.date} at {instance.time}.")

        elif instance.status == "confirmed":
            message = f"Hello {instance.patient.get_full_name()}, your appointment with Dr. {instance.doctor.user.get_full_name()} has been confirmed for {instance.date} at {instance.time}."
            send_sms(patient_number, message)

        elif instance.status == "cancelled":
            message = f"Hello {instance.patient.get_full_name()}, your appointment with Dr. {instance.doctor.user.get_full_name()} has been cancelled."
            send_sms(patient_number, message)
