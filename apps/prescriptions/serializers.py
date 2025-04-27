from rest_framework import serializers
from .models import MedicalHistory, Prescription, MedicalReport
from config.utils import AESEncryption

aes = AESEncryption()

class MedicalHistorySerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)

    class Meta:
        model = MedicalHistory
        fields = '__all__'

class PrescriptionSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.full_name", read_only=True)
    decrypted_prescription = serializers.SerializerMethodField()

    class Meta:
        model = Prescription
        fields = '__all__'

    def validate_encrypted_prescription(self, value):
        """Encrypt prescription before saving"""
        return aes.encrypt(value)  # Encrypt before saving

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

    class Meta:
        model = MedicalReport
        fields = '__all__'

    def validate_encrypted_diagnosis(self, value):
        """
        DO NOT encrypt here because the frontend already does it.
        """
        return value  

    def validate_encrypted_treatment_plan(self, value):
        return value  

    def validate_encrypted_notes(self, value):
        return value  

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
        if self.context.get("request").user == obj.patient.user:
            return obj.get_decrypted_notes()
        return "Restricted Access"
