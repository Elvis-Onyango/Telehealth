from datetime import datetime

from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.users.models import DoctorProfile, PatientProfile

from .models import Appointment, Billing, Hospital, HospitalAdministrator
from apps.pharmacy.models import Order, PharmacyItem


class HospitalForm(forms.ModelForm):
    class Meta:
        model = Hospital
        fields = ["name", "address", "contact", "email"]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
        }


class HospitalAdministratorCreationForm(forms.Form):
    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField(required=False)
    password = forms.CharField(widget=forms.PasswordInput)
    hospital = forms.ModelChoiceField(queryset=Hospital.objects.none())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["hospital"].queryset = Hospital.objects.order_by("name")

    def clean_username(self):
        username = self.cleaned_data["username"]
        if get_user_model().objects.filter(username=username).exists():
            raise ValidationError("A user with this username already exists.")
        return username

    def clean_password(self):
        password = self.cleaned_data["password"]
        password_validation.validate_password(password)
        return password

    @transaction.atomic
    def save(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username=self.cleaned_data["username"],
            password=self.cleaned_data["password"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            email=self.cleaned_data["email"],
            role="admin",
            is_staff=False,
        )
        return HospitalAdministrator.objects.create(
            user=user,
            hospital=self.cleaned_data["hospital"],
        )


class HospitalAdministratorUpdateForm(forms.Form):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField(required=False)
    hospital = forms.ModelChoiceField(queryset=Hospital.objects.none())
    is_active = forms.BooleanField(required=False, label="Account active")

    def __init__(self, *args, instance, **kwargs):
        self.instance = instance
        super().__init__(*args, **kwargs)
        self.fields["hospital"].queryset = Hospital.objects.order_by("name")
        if not self.is_bound:
            self.initial.update(
                first_name=instance.user.first_name,
                last_name=instance.user.last_name,
                email=instance.user.email,
                hospital=instance.hospital_id,
                is_active=instance.user.is_active,
            )

    @transaction.atomic
    def save(self):
        user = self.instance.user
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        user.is_active = self.cleaned_data["is_active"]
        user.save(update_fields=["first_name", "last_name", "email", "is_active"])
        self.instance.hospital = self.cleaned_data["hospital"]
        self.instance.save(update_fields=["hospital"])
        return self.instance


class DoctorAssignmentForm(forms.Form):
    doctor = forms.ModelChoiceField(queryset=DoctorProfile.objects.none())

    def __init__(self, *args, hospital, **kwargs):
        super().__init__(*args, **kwargs)
        self.hospital = hospital
        self.fields["doctor"].queryset = (
            DoctorProfile.objects.filter(hospital__isnull=True)
            .select_related("user")
            .order_by("user__last_name", "user__first_name")
        )

    def save(self):
        doctor = self.cleaned_data["doctor"]
        doctor.hospital = self.hospital
        doctor.save(update_fields=["hospital"])
        return doctor


class DoctorProfileManagementForm(forms.ModelForm):
    class Meta:
        model = DoctorProfile
        fields = [
            "specialization",
            "consultation_fee",
            "years_of_experience",
            "license_number",
            "available_days",
        ]
        widgets = {
            "available_days": forms.CheckboxSelectMultiple(),
        }


class HospitalAppointmentForm(forms.ModelForm):
    payment_method = forms.ChoiceField(choices=Billing.PAYMENT_METHODS)

    class Meta:
        model = Appointment
        fields = ["patient", "doctor", "date", "time", "type", "status"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "time": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, hospital, **kwargs):
        self.hospital = hospital
        super().__init__(*args, **kwargs)
        patients = PatientProfile.objects.filter(
            Q(appointments__hospital=hospital)
            | Q(assigned_doctors__hospital=hospital)
        ).distinct()
        if self.instance.pk:
            patients = PatientProfile.objects.filter(
                Q(appointments__hospital=hospital)
                | Q(assigned_doctors__hospital=hospital)
                | Q(pk=self.instance.patient_id)
            ).distinct()
        self.fields["patient"].queryset = patients.select_related("user").order_by(
            "user__last_name",
            "user__first_name",
        )
        doctors = DoctorProfile.objects.filter(hospital=hospital).select_related("user")
        if self.instance.pk and self.instance.doctor_id:
            doctors = DoctorProfile.objects.filter(
                Q(hospital=hospital) | Q(pk=self.instance.doctor_id)
            ).select_related("user")
        self.fields["doctor"].queryset = doctors.order_by(
            "user__last_name",
            "user__first_name",
        )
        self.fields["status"].choices = [
            choice for choice in Appointment.STATUS_CHOICES if choice[0] != "cancelled"
        ]
        if self.instance.pk:
            try:
                self.initial["payment_method"] = self.instance.billing.payment_method
            except Billing.DoesNotExist:
                self.initial["payment_method"] = "mpesa"

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get("doctor")
        date = cleaned_data.get("date")
        time = cleaned_data.get("time")
        if doctor and doctor.hospital_id != self.hospital.pk:
            if not self.instance.pk or doctor.pk != self.instance.doctor_id:
                self.add_error("doctor", "Choose a doctor assigned to this hospital.")

        if not self.instance.pk and date and time:
            appointment_at = timezone.make_aware(
                datetime.combine(date, time),
                timezone.get_current_timezone(),
            )
            if appointment_at <= timezone.now():
                self.add_error("date", "New appointments must be scheduled in the future.")

        if doctor and date and time:
            weekday = date.strftime("%A").lower()
            available_days = set(doctor.available_days.values_list("day", flat=True))
            if available_days and weekday not in available_days:
                self.add_error("date", "This doctor is not available on the selected day.")
            if doctor.availabilities.exists() and not doctor.availabilities.filter(
                day=weekday,
                start_time__lte=time,
                end_time__gt=time,
            ).exists():
                self.add_error("time", "This doctor is not available at the selected time.")

            conflicting = Appointment.objects.filter(
                doctor=doctor,
                date=date,
                time=time,
                is_active=True,
            )
            if self.instance.pk:
                conflicting = conflicting.exclude(pk=self.instance.pk)
            if conflicting.exists():
                self.add_error("time", "This doctor is already booked at that time.")
        return cleaned_data

    @transaction.atomic
    def save(self, commit=True, processed_by=None):
        appointment = super().save(commit=False)
        appointment.hospital = self.hospital
        is_new = appointment.pk is None
        if commit:
            appointment.save()
            self.save_m2m()
            if is_new:
                Billing.objects.create(
                    appointment=appointment,
                    total_fee=appointment.doctor.consultation_fee,
                    payment_method=self.cleaned_data["payment_method"],
                    payment_status="pending",
                    processed_by=processed_by,
                )
            elif hasattr(appointment, "billing"):
                appointment.billing.payment_method = self.cleaned_data["payment_method"]
                appointment.billing.save(update_fields=["payment_method"])
        return appointment


class BillingManagementForm(forms.ModelForm):
    class Meta:
        model = Billing
        fields = ["payment_method", "payment_status", "transaction_id", "payment_date"]
        widgets = {
            "payment_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("payment_status") == "paid" and not cleaned_data.get("payment_date"):
            cleaned_data["payment_date"] = timezone.now()
        return cleaned_data


class PharmacyItemManagementForm(forms.ModelForm):
    class Meta:
        model = PharmacyItem
        fields = ["name", "description", "price", "stock", "image"]

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price < 0:
            raise ValidationError("Price cannot be negative.")
        return price


class PharmacyOrderManagementForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["status"]
