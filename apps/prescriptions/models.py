from django.db import models
from apps.users.models import User, DoctorProfile, PatientProfile
from apps.appointments.models import Appointment
from config.utils import AESEncryption
import json

aes = AESEncryption()

class MedicalHistory(models.Model):
    """
    Stores detailed medical history for each patient.
    """
    patient = models.OneToOneField(
        PatientProfile, on_delete=models.CASCADE, related_name="medical_history_entry"
    )  
    allergies = models.TextField(blank=True, null=True)
    chronic_diseases = models.TextField(blank=True, null=True)
    past_surgeries = models.TextField(blank=True, null=True)
    family_medical_history = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Medical History of {self.patient.user.get_full_name()}"


class Prescription(models.Model):
    """
    Stores encrypted prescriptions linked to medical history.
    Each prescription is linked to a doctor and patient.
    """
    medical_history = models.ForeignKey(
        MedicalHistory, on_delete=models.CASCADE, related_name="prescriptions", null=True, blank=True
    )
    patient = models.ForeignKey(
        PatientProfile, on_delete=models.CASCADE, related_name="prescriptions"
    )  
    doctor = models.ForeignKey(
        DoctorProfile, on_delete=models.CASCADE, related_name="doctor_prescriptions"
    )
    appointment = models.ForeignKey(
        Appointment, on_delete=models.CASCADE, related_name="appointment_prescriptions", blank=True, null=True
    )
    encrypted_prescription = models.TextField()
    date_issued = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """
        DO NOT encrypt again because the frontend already does it.
        Just save the encrypted data as received from the frontend.
        """
        super().save(*args, **kwargs)

    def get_decrypted_prescription(self):
        """
        Decrypt prescription for authorized users.
        """
        try:
            decrypted = aes.decrypt(self.encrypted_prescription)
            return json.loads(decrypted)  # Decrypt only once
        except Exception as e:
            return "Decryption Failed"  # Handle decryption errors properly

    def __str__(self):
        return f"Prescription for {self.patient.user.get_full_name()} by Dr. {self.doctor.user.get_full_name()} (Issued: {self.date_issued.date()})"


class MedicalReport(models.Model):
    """
    Stores medical reports for patients, including uploaded lab results, X-rays, and doctor observations.
    """
    patient = models.ForeignKey(
        PatientProfile, on_delete=models.CASCADE, related_name="medical_reports"
    )
    doctor = models.ForeignKey(
        DoctorProfile, on_delete=models.SET_NULL, null=True, related_name="issued_reports"
    )
    appointment = models.ForeignKey(
        Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name="medical_reports"
    )
    report_file = models.FileField(upload_to="medical_reports/", blank=True, null=True)
    diagnosis = models.TextField(blank=True, null=True)  # Encrypted
    treatment_plan = models.TextField(blank=True, null=True)  # Encrypted
    encrypted_notes = models.TextField(blank=True, null=True)  # Encrypted
    date_issued = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """
         Encrypt sensitive data before saving.
        """
        if self.diagnosis:
            self.diagnosis = aes.encrypt(self.diagnosis)
        if self.treatment_plan:
            self.treatment_plan = aes.encrypt(self.treatment_plan)
        if self.encrypted_notes:
            self.encrypted_notes = aes.encrypt(self.encrypted_notes)

        super().save(*args, **kwargs)

    def get_decrypted_diagnosis(self):
        """
         Decrypt diagnosis.
        """
        try:
            return aes.decrypt(self.diagnosis)
        except Exception:
            return "Decryption Failed"

    def get_decrypted_treatment_plan(self):
        """
         Decrypt treatment plan.
        """
        try:
            return aes.decrypt(self.treatment_plan)
        except Exception:
            return "Decryption Failed"

    def get_decrypted_notes(self):
        """
        Decrypt additional notes.
        """
        try:
            return aes.decrypt(self.encrypted_notes)
        except Exception:
            return "Decryption Failed"

    def __str__(self):
        return f"Medical Report - {self.patient.user.get_full_name()} by Dr. {self.doctor.user.get_full_name()}"
