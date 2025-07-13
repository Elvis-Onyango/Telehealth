from django.db import models
from django.utils import timezone
from apps.users.models import User

class Message(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('file', 'File'),
        ('link', 'Link'),
        ('dosage', 'Dosage'),
        ('meeting', 'Meeting Link'),
    ]

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    
    content = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='chat_files/', blank=True, null=True)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')

    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.sender.username} ➜ {self.recipient.username}"
