from django.db import models
from django.utils.timezone import now
from apps.users.models import DoctorProfile, PatientProfile, User

# =================== Hospital Model ===================
class Hospital(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    contact = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True, blank=True, null=True)

    def __str__(self):
        return self.name

# =================== Appointment Model ===================
class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )

    APPOINTMENT_TYPE_CHOICES = (
        ('physical', 'Physical'),
        ('virtual', 'Virtual'),
    )

    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name="appointments")
    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, related_name="appointments", blank=True, null=True)

    date = models.DateField(default=now)
    time = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    type = models.CharField(max_length=10, choices=APPOINTMENT_TYPE_CHOICES, default='physical')

    notes = models.TextField(blank=True, null=True)
    reschedule_reason = models.TextField(blank=True, null=True)
    was_rescheduled = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)  # For soft delete/future filtering

    def __str__(self):
        return f"Appointment with {self.doctor.user.get_full_name()} on {self.date} at {self.time}"

    class Meta:
        ordering = ['-date', '-time']  # Show latest first
        unique_together = ('doctor', 'date', 'time')  # Prevent double booking at DB level

# =================== Billing Model ===================
class Billing(models.Model):
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

    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default="pending")
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateTimeField(null=True, blank=True)

    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Billing for Appointment ID {self.appointment.id} - Status: {self.payment_status}"
