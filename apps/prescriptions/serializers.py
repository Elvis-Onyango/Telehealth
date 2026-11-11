from django.urls import reverse
from rest_framework import serializers
from django.db.models import Q

from apps.appointments.models import Appointment
from apps.users.models import PatientProfile

from .models import MedicalHistory, Prescription, MedicalReport
from config.utils import AESEncryption

aes = AESEncryption()

class MedicalHistorySerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)

    class Meta:
        model = MedicalHistory
        fields = '__all__'
        read_only_fields = ["patient"]

class PrescriptionSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.full_name", read_only=True)
    decrypted_prescription = serializers.SerializerMethodField()

    class Meta:
        model = Prescription
        fields = '__all__'
        read_only_fields = ["doctor"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        doctor = getattr(request.user, "doctor_profile", None) if request else None
        patients = PatientProfile.objects.none()
        if doctor:
            patients = PatientProfile.objects.filter(
                Q(assigned_doctors=doctor) | Q(appointments__doctor=doctor)
            ).distinct()
        self.fields["patient"].queryset = patients
        self.fields["medical_history"].queryset = MedicalHistory.objects.filter(
            patient__in=patients
        )
        self.fields["appointment"].queryset = Appointment.objects.filter(
            doctor=doctor,
            patient__in=patients,
        ) if doctor else Appointment.objects.none()

    def validate_encrypted_prescription(self, value):
        """Encrypt prescription before saving"""
        return aes.encrypt(value)  # Encrypt before saving

    def validate(self, attrs):
        attrs = super().validate(attrs)
        patient = attrs.get("patient", getattr(self.instance, "patient", None))
        medical_history = attrs.get(
            "medical_history",
            getattr(self.instance, "medical_history", None),
        )
        appointment = attrs.get("appointment", getattr(self.instance, "appointment", None))
        request = self.context.get("request")
        doctor = getattr(request.user, "doctor_profile", None) if request else None

        if medical_history and patient and medical_history.patient_id != patient.pk:
            raise serializers.ValidationError(
                {"medical_history": "Choose a history belonging to this patient."}
            )
        if appointment and patient and appointment.patient_id != patient.pk:
            raise serializers.ValidationError(
                {"appointment": "Choose an appointment belonging to this patient."}
            )
        if appointment and doctor and appointment.doctor_id != doctor.pk:
            raise serializers.ValidationError(
                {"appointment": "Choose an appointment assigned to you."}
            )
        return attrs

    def get_decrypted_prescription(self, obj):
        request = self.context.get("request")
        if request and request.user == obj.patient.user:
            return obj.get_decrypted_prescription()
        return "Restricted Access"


class MedicalReportSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.full_name", read_only=True)
    decrypted_diagnosis = serializers.SerializerMethodField()
    decrypted_treatment_plan = serializers.SerializerMethodField()
    decrypted_notes = serializers.SerializerMethodField()
    report_file = serializers.SerializerMethodField()

    class Meta:
        model = MedicalReport
        fields = '__all__'
        read_only_fields = ["doctor"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        doctor = getattr(request.user, "doctor_profile", None) if request else None
        patients = PatientProfile.objects.none()
        if doctor:
            patients = PatientProfile.objects.filter(
                Q(assigned_doctors=doctor) | Q(appointments__doctor=doctor)
            ).distinct()
        self.fields["patient"].queryset = patients
        self.fields["appointment"].queryset = Appointment.objects.filter(
            doctor=doctor,
            patient__in=patients,
        ) if doctor else Appointment.objects.none()

    def validate_encrypted_diagnosis(self, value):
        """
        DO NOT encrypt here because the frontend already does it.
        """
        return value  

    def validate_encrypted_treatment_plan(self, value):
        return value  

    def validate_encrypted_notes(self, value):
        return value  

    def validate(self, attrs):
        attrs = super().validate(attrs)
        patient = attrs.get("patient", getattr(self.instance, "patient", None))
        appointment = attrs.get("appointment", getattr(self.instance, "appointment", None))
        if appointment and patient and appointment.patient_id != patient.pk:
            raise serializers.ValidationError(
                {"appointment": "Choose an appointment belonging to this patient."}
            )
        request = self.context.get("request")
        doctor = getattr(request.user, "doctor_profile", None) if request else None
        if appointment and doctor and appointment.doctor_id != doctor.pk:
            raise serializers.ValidationError(
                {"appointment": "Choose an appointment assigned to you."}
            )
        return attrs

    def get_decrypted_diagnosis(self, obj):
        """
        Only decrypt if the request is from the patient.
        """
        request = self.context.get("request")
        if request and request.user == obj.patient.user:
            return obj.get_decrypted_diagnosis()
        return "Restricted Access"

    def get_decrypted_treatment_plan(self, obj):
        if self.context.get("request").user == obj.patient.user:
            return obj.get_decrypted_treatment_plan()
        return "Restricted Access"

    def get_decrypted_notes(self, obj):
        request = self.context.get("request")
        if request and request.user == obj.patient.user:
            return obj.get_decrypted_notes()
        return "Restricted Access"

    def get_report_file(self, obj):
        if not obj.report_file:
            return None
        url = reverse("medical-report-download", kwargs={"pk": obj.pk})
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url
