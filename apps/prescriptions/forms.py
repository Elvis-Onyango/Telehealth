from django import forms
from django.db import models

from apps.appointments.models import Appointment
from apps.users.models import PatientProfile

from .models import MedicalReport, SymptomIntake


class SymptomIntakeForm(forms.ModelForm):
    class Meta:
        model = SymptomIntake
        fields = [
            "primary_symptoms",
            "symptom_duration",
            "severity",
            "associated_factors",
            "notes",
        ]
        widgets = {
            "primary_symptoms": forms.Textarea(attrs={"rows": 3}),
            "associated_factors": forms.Textarea(attrs={"rows": 2}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class MedicalReportCreationForm(forms.ModelForm):
    class Meta:
        model = MedicalReport
        fields = [
            "patient",
            "appointment",
            "diagnosis",
            "treatment_plan",
            "encrypted_notes",
            "report_file",
        ]
        labels = {
            "encrypted_notes": "Clinical notes",
            "report_file": "Lab result or report file",
        }
        widgets = {
            "diagnosis": forms.Textarea(attrs={"rows": 3}),
            "treatment_plan": forms.Textarea(attrs={"rows": 3}),
            "encrypted_notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, doctor, **kwargs):
        super().__init__(*args, **kwargs)
        patients = PatientProfile.objects.filter(
            models.Q(assigned_doctors=doctor)
            | models.Q(primary_doctor=doctor)
            | models.Q(appointments__doctor=doctor)
        ).distinct()
        self.fields["patient"].queryset = patients.select_related("user").order_by(
            "user__last_name",
            "user__first_name",
        )
        self.fields["appointment"].queryset = Appointment.objects.filter(
            doctor=doctor,
            patient__in=patients,
        ).select_related("patient__user").order_by("-date", "-time")
        self.fields["appointment"].required = False

    def clean(self):
        cleaned_data = super().clean()
        patient = cleaned_data.get("patient")
        appointment = cleaned_data.get("appointment")
        if appointment and patient and appointment.patient_id != patient.pk:
            self.add_error("appointment", "Choose an appointment for this patient.")
        return cleaned_data
