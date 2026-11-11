from django.db import models
from django.db.models import Q
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


class HospitalAdministrator(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="hospital_administration",
    )
    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.PROTECT,
        related_name="administrators",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.hospital.name}"


# =================== Appointment Model ===================
class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('no_show', 'No-show'),
    )

    APPOINTMENT_TYPE_CHOICES = (
        ('physical', 'Physical'),
        ('virtual', 'Virtual'),
    )

    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name="appointments")
    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, related_name="appointments", blank=True, null=True)
    follow_up_of = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='follow_ups',
    )

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

    def reschedule(self, new_date=None, new_time=None, reason="", status='pending'):
        if new_date is not None:
            self.date = new_date
        if new_time is not None:
            self.time = new_time
        if reason:
            self.reschedule_reason = reason
        self.was_rescheduled = True
        self.status = status
        self.is_active = True
        self.save()
        return self

    def mark_no_show(self):
        self.status = 'no_show'
        self.save(update_fields=['status', 'updated_at'])
        return self

    def create_follow_up(self, new_date, new_time, doctor=None, hospital=None, patient=None, notes=None, appointment_type=None):
        follow_up = Appointment.objects.create(
            patient=patient or self.patient,
            doctor=doctor or self.doctor,
            hospital=hospital or self.hospital,
            date=new_date,
            time=new_time,
            status='pending',
            type=appointment_type or self.type,
            notes=notes or f"Follow-up for appointment #{self.pk}",
            follow_up_of=self,
        )
        return follow_up

    class Meta:
        ordering = ['-date', '-time']  # Show latest first
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "date", "time"],
                condition=Q(is_active=True),
                name="unique_active_doctor_appointment_slot",
            ),
        ]

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
