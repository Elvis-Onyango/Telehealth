from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

# =================== Custom User Manager ===================
class CustomUserManager(BaseUserManager):
    def _normalize_phone(self, value):
        if value is None:
            return None
        value = str(value).strip()
        return value or None

    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("The username field must be set.")

        extra_fields.setdefault("role", "patient")
        extra_fields["phone"] = self._normalize_phone(extra_fields.get("phone"))

        if password is None:
            raise ValueError("The password field must be set.")

        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, password, **extra_fields)

# =================== Custom User Model ===================
class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
    )
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
    )

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    role = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, blank=True, null=True)
    phone = models.CharField(max_length=15, unique=True, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    profile_picture = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if self.phone is not None:
            self.phone = str(self.phone).strip() or None

        if not self.role:
            self.role = 'admin' if self.is_superuser else 'patient'

        super().save(*args, **kwargs)

    def is_doctor(self):
        return self.role == 'doctor'

    def is_patient(self):
        return self.role == 'patient'

    def get_messaging_contacts(self):
        from apps.messaging.models import Message  # Avoid circular import

        if self.role == 'doctor':
            try:
                patients = self.doctor_profile.get_patients()
                contacts = []
                for patient in patients:
                    user = patient.user
                    last_message = Message.objects.filter(
                        models.Q(sender=self, recipient=user) |
                        models.Q(sender=user, recipient=self)
                    ).order_by('-timestamp').first()

                    unread_count = Message.objects.filter(
                        sender=user,
                        recipient=self,
                        is_read=False
                    ).count()

                    contacts.append({
                        'id': user.id,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'last_message': last_message,
                        'unread_count': unread_count
                    })
                return contacts
            except DoctorProfile.DoesNotExist:
                return []

        elif self.role == 'patient':
            try:
                doctors = self.patient_profile.get_doctors()
                contacts = []
                for doctor in doctors:
                    user = doctor.user
                    last_message = Message.objects.filter(
                        models.Q(sender=self, recipient=user) |
                        models.Q(sender=user, recipient=self)
                    ).order_by('-timestamp').first()

                    unread_count = Message.objects.filter(
                        sender=user,
                        recipient=self,
                        is_read=False
                    ).count()

                    contacts.append({
                        'id': user.id,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'last_message': last_message,
                        'unread_count': unread_count
                    })
                return contacts
            except PatientProfile.DoesNotExist:
                return []
        return []

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.username

# =================== Weekday Model ===================
class Weekday(models.Model):
    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    day = models.CharField(max_length=10, choices=DAY_CHOICES, unique=True)

    def __str__(self):
        return self.day.capitalize()

# =================== Doctor Profile Model ===================
class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="doctor_profile")
    specialization = models.CharField(max_length=100)
    patients = models.ManyToManyField('PatientProfile', blank=True, related_name="assigned_doctors")
    hospital = models.ForeignKey('appointments.Hospital', on_delete=models.SET_NULL, null=True)
    available_days = models.ManyToManyField(Weekday, blank=True, related_name="doctors")
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    years_of_experience = models.PositiveIntegerField(default=0)
    license_number = models.CharField(max_length=50, unique=True)
    certifications = models.FileField(upload_to="doctor_certifications/", blank=True, null=True)
    profile_picture = models.ImageField(upload_to="doctor_pictures/", blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.user.is_superuser or self.user.role != 'doctor':
            raise ValidationError("Only users with the 'doctor' role can have a DoctorProfile.")
        super().save(*args, **kwargs)

    def get_patients(self):
        return self.patients.all()

    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name} - {self.specialization}"

    def get_available_times_for(self, day):
        return self.availabilities.filter(day=day.lower()).first()

    def is_available_on(self, day, time):
        slot = self.get_available_times_for(day)
        if slot and slot.start_time <= time <= slot.end_time:
            return True
        return False
                 
class DoctorAvailability(models.Model):
    doctor = models.ForeignKey('DoctorProfile', on_delete=models.CASCADE, related_name="availabilities")
    day = models.CharField(
        max_length=10,
        choices=[
            ('monday', 'Monday'),
            ('tuesday', 'Tuesday'),
            ('wednesday', 'Wednesday'),
            ('thursday', 'Thursday'),
            ('friday', 'Friday'),
            ('saturday', 'Saturday'),
            ('sunday', 'Sunday'),
        ]
    )
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ('doctor', 'day')  # Prevent duplicate entries for same day

    def __str__(self):
        return f"{self.doctor.user.get_full_name()} - {self.day.title()} ({self.start_time} to {self.end_time})"



# =================== Patient Profile Model ===================
class PatientProfile(models.Model):
    BLOOD_TYPE_CHOICES = (
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="patient_profile")
    primary_doctor = models.ForeignKey(DoctorProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="primary_patients")
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=User.GENDER_CHOICES, blank=True, null=True)
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPE_CHOICES, blank=True, null=True)
    current_medications = models.ManyToManyField('prescriptions.MedicalReport', blank=True, related_name="patient_profile")
    medical_history = models.OneToOneField('prescriptions.MedicalHistory', on_delete=models.SET_NULL, null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to="patient_pictures/", blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.user.is_superuser or self.user.role != 'patient':
            raise ValidationError("Only users with the 'patient' role can have a PatientProfile.")
        super().save(*args, **kwargs)

    def get_doctors(self):
        return [self.primary_doctor] if self.primary_doctor else []

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
