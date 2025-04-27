from django.db import models
from django.utils.timezone import now
from apps.users.models import User, DoctorProfile,PatientProfile
from django.utils import timezone





class Hospital(models.Model):
    """
    Stores hospital details where doctors are located.
    """
    name = models.CharField(max_length=255)
    address = models.TextField()
    contact = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True, blank=True, null=True)

    def __str__(self):
        return self.name

class Appointment(models.Model):
    """
    Stores patient-doctor appointments with scheduling details.
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )

    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name="appointments")
    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, related_name="appointments", blank=True, null=True)
    
    date = models.DateField(default=now)  # Default to current date
    time = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Track updates
    reschedule_reason = models.TextField(blank=True, null=True)  # Reason for rescheduling

    def __str__(self):
        return f"Appointment with {self.doctor.user.get_full_name()} on {self.date} at {self.time}"

class Billing(models.Model):
    """
    Handles payment details for medical consultations.
    """
    PAYMENT_METHODS = (
        ('mpesa', 'M-Pesa'),
        ('card', 'Card'),
        ('insurance', 'Insurance'), 
    )

    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    )

    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name="billing")
    total_fee = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default="pending")
    payment_date = models.DateTimeField(null=True, blank=True)
