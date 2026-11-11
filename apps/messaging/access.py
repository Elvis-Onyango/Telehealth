from django.core.exceptions import ObjectDoesNotExist

from apps.appointments.models import Appointment


def can_message(user, contact):
    if user == contact or not user.is_active or not contact.is_active:
        return False

    if user.role == "doctor" and contact.role == "patient":
        try:
            return (
                user.doctor_profile.patients.filter(user=contact).exists()
                or Appointment.objects.filter(
                    doctor__user=user,
                    patient__user=contact,
                ).exists()
            )
        except ObjectDoesNotExist:
            return False

    if user.role == "patient" and contact.role == "doctor":
        try:
            return (
                contact.doctor_profile.patients.filter(user=user).exists()
                or Appointment.objects.filter(
                    doctor__user=contact,
                    patient__user=user,
                ).exists()
            )
        except ObjectDoesNotExist:
            return False

    return False
