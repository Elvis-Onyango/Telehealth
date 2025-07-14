from rest_framework import serializers
from .models import  VideoCall

class AppointmentSerializer(serializers.ModelSerializer):
    video_call_link = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = ['id', 'doctor', 'patient', 'date', 'time', 'type', 'status', 'video_call_link']

    def get_video_call_link(self, obj):
        if hasattr(obj, 'video_call'):
            return obj.video_call.meeting_link
        return None


