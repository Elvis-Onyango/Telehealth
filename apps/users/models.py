from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.exceptions import ValidationError

# =================== Custom User Manager (No Email Required) ===================
class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
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

    def is_doctor(self):
        return self.role == 'doctor'

    def is_patient(self):
        return self.role == 'patient'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"  # Full name display

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
    license_number = models.CharField(max_length=50, unique=True, blank=False, null=False)
    certifications = models.FileField(upload_to="doctor_certifications/", blank=True, null=True)
    profile_picture = models.ImageField(upload_to="doctor_pictures/", blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.user.is_superuser or self.user.role != 'doctor':
            raise ValidationError("Only users with the 'doctor' role can have a DoctorProfile.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name} - {self.specialization}"

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

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='message_files/', blank=True, null=True)
    video = models.FileField(upload_to='message_videos/', blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    message_type = models.CharField(
        max_length=10,
        choices=[
            ('text', 'Text'),
            ('image', 'Image'),
            ('video', 'Video'),
            ('file', 'File'),
            ('link', 'Link')
        ],
        default='text'
    )

    class Meta:
        ordering = ['-timestamp']

    def clean(self):
        # Validate doctor-patient relationship
        if not ((self.sender.role == 'doctor' and self.recipient.role == 'patient') or 
                (self.sender.role == 'patient' and self.recipient.role == 'doctor')):
            raise ValidationError("Messages can only be exchanged between doctors and patients")
        
        # Validate message has content
        if not any([self.content, self.file, self.video, self.link]):
            raise ValidationError("Message must have content, file, video, or link")

    def save(self, *args, **kwargs):
        # Determine message type
        if self.video:
            self.message_type = 'video'
        elif self.file:
            if self.file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                self.message_type = 'image'
            else:
                self.message_type = 'file'
        elif self.link:
            self.message_type = 'link'
        
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sender} → {self.recipient}: {self.message_type}"