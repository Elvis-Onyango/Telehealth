from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime

from config.utils import send_sms
from apps.appointments.models import Appointment
from apps.videoconferencing.models import VideoCall


@receiver(post_save, sender=Appointment)
def send_appointment_notification(sender, instance, created, **kwargs):
    """
    Sends SMS notifications when an appointment is booked, confirmed, or cancelled.
    """
    try:
        patient_number = instance.patient.user.phone
        doctor_number = instance.doctor.user.phone

        if created:
            msg = f"Hello {instance.patient.user.get_full_name()}, your appointment with Dr. {instance.doctor.user.get_full_name()} is scheduled for {instance.date} at {instance.time}. Thank you!"
            send_sms(patient_number, msg)
            send_sms(doctor_number, f"New appointment with {instance.patient.user.get_full_name()} on {instance.date} at {instance.time}.")

        elif instance.status == "confirmed":
            msg = f"Hello {instance.patient.user.get_full_name()}, your appointment with Dr. {instance.doctor.user.get_full_name()} has been confirmed for {instance.date} at {instance.time}."
            send_sms(patient_number, msg)

        elif instance.status == "cancelled":
            msg = f"Hello {instance.patient.user.get_full_name()}, your appointment with Dr. {instance.doctor.user.get_full_name()} has been cancelled."
            send_sms(patient_number, msg)

    except Exception as e:
        print(f"⚠️ SMS sending failed: {e}")


@receiver(post_save, sender=Appointment)
def create_video_call_for_virtual_appointment(sender, instance, created, **kwargs):
    """
    Automatically create a Jitsi video call for virtual appointments.
    """
    try:
        if instance.type == 'virtual' and created and not hasattr(instance, 'video_call'):
            scheduled_time = datetime.combine(instance.date, instance.time)

            video_call = VideoCall.objects.create(
                appointment=instance,
                host=instance.doctor.user,
                scheduled_time=scheduled_time,
                duration=90  # You can customize this or make it dynamic
            )
            video_call.participants.set([instance.patient.user])
            print(f"📹 Video call created for virtual appointment: {video_call.meeting_link}")

    except Exception as e:
        print(f"⚠️ Failed to create video call: {e}")
