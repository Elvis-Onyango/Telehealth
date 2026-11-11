from django.db import models
from apps.users.models import User, DoctorProfile, PatientProfile
from apps.appointments.models import Appointment
from config.utils import AESEncryption
import json

aes = AESEncryption()


def build_visit_summary_pdf(summary_lines):
    """Create a minimal valid PDF payload containing the visit summary text."""
    content = []
    y = 760
    for line in summary_lines:
        text = str(line).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        content.append(f"BT /F1 12 Tf 72 {y} Td ({text}) Tj ET")
        y -= 18
    stream = "\n".join(content)
    objects = [
        "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n",
        f"4 0 obj\n<< /Length {len(stream.encode('utf-8'))} >>\nstream\n{stream}\nendstream\nendobj\n",
        "5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]

    pdf = b"%PDF-1.4\n"
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf += f"{len(offsets)-1} 0 obj\n".encode("utf-8") + obj.encode("utf-8")
    xref_start = len(pdf)
    pdf += f"xref\n0 {len(objects) + 1}\n".encode("utf-8")
    pdf += b"0000000000 65535 f \n"
    for offset in offsets[1:]:
        pdf += f"{offset:010d} 00000 n \n".encode("ascii")
    pdf += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode("utf-8")
    return pdf


class SymptomIntake(models.Model):
    SEVERITY_CHOICES = (
        ("mild", "Mild"),
        ("moderate", "Moderate"),
        ("severe", "Severe"),
    )

    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="symptom_intakes",
    )
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name="symptom_intakes",
        blank=True,
        null=True,
    )
    primary_symptoms = models.TextField()
    symptom_duration = models.CharField(max_length=100, blank=True, default="")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="moderate")
    associated_factors = models.TextField(blank=True, default="")
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Symptom intake for {self.patient.user.get_full_name()}"


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
