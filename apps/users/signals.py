from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, DoctorProfile, PatientProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if not created:
        return

    # Avoid creating profiles for admins/superusers
    if instance.is_superuser or instance.role not in ['doctor', 'patient']:
        return

    # Create Doctor Profile
    if instance.role == 'doctor' and not hasattr(instance, 'doctor_profile'):
        DoctorProfile.objects.create(
            user=instance,
            specialization="General",  # or default based on your app logic
            license_number=f"TEMP-{instance.id}"  # safe unique fallback
        )

    # Create Patient Profile
    elif instance.role == 'patient' and not hasattr(instance, 'patient_profile'):
        PatientProfile.objects.create(user=instance)
