from django.db import models
from apps.users.models import User, DoctorProfile, PatientProfile

class Conversation(models.Model):
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='conversations')
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['doctor', 'patient'], name='unique_doctor_patient')
        ]

    def __str__(self):
        return f"Dr. {self.doctor.user.get_full_name()} ↔ {self.patient.user.get_full_name()}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages',null=True,blank=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages',null=True, blank=True)
    content = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='chat_files/', blank=True, null=True)
    file_type = models.CharField(max_length=50, blank=True, null=True)  # e.g., 'image', 'pdf', 'xray'
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender.get_full_name()} in {self.conversation}"
