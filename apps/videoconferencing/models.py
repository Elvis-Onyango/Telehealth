from django.db import models
from django.conf import settings  
import uuid

from apps.appointments.models import Appointment

class VideoCall(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='video_call')
    host = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="hosted_calls", on_delete=models.CASCADE)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="video_calls")
    meeting_link = models.URLField(blank=True)
    scheduled_time = models.DateTimeField()
    duration = models.IntegerField(help_text="Duration in minutes")
    meeting_id = models.CharField(max_length=100, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.meeting_id:
            self.meeting_id = str(uuid.uuid4())
            self.meeting_link = f"https://meet.jit.si/{self.meeting_id}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Video Call for {self.appointment}"


  



