from django.db import models
from django.conf import settings  
import uuid

class VideoCall(models.Model):
    host = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="hosted_calls", on_delete=models.CASCADE)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="video_calls")
    meeting_link = models.URLField(blank=True)  # Store Jitsi URL
    scheduled_time = models.DateTimeField()
    duration = models.IntegerField(help_text="Duration in minutes")
    meeting_id = models.CharField(max_length=100, unique=True, blank=True)  # Unique Jitsi Room Name

    def save(self, *args, **kwargs):
        if not self.meeting_id:
            self.meeting_id = str(uuid.uuid4())  # Generate unique room name
            self.meeting_link = f"https://meet.jit.si/{self.meeting_id}"  # Jitsi URL
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Video Call by {self.host} at {self.scheduled_time}"



  



