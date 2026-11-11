from rest_framework import serializers
from django.urls import reverse
from apps.appointments.models import Appointment
from .models import VideoCall


def get_meeting_page_url(obj, request=None):
    meeting_url = reverse(
        "videoconferencing:video_meeting",
        kwargs={"meeting_id": obj.meeting_id},
    )
    return request.build_absolute_uri(meeting_url) if request else meeting_url


class AppointmentSerializer(serializers.ModelSerializer):
    video_call_link = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = ['id', 'doctor', 'patient', 'date', 'time', 'type', 'status', 'video_call_link']

    def get_video_call_link(self, obj):
        if hasattr(obj, 'video_call'):
            return get_meeting_page_url(
                obj.video_call,
                self.context.get("request"),
            )
        return None


class VideoCallSerializer(serializers.ModelSerializer):
    appointment = AppointmentSerializer(read_only=True)
    meeting_link = serializers.SerializerMethodField()

    class Meta:
        model = VideoCall
        fields = [
            'id',
            'appointment',
            'host',
            'participants',
            'meeting_link',
            'scheduled_time',
            'duration',
            'meeting_id',
        ]

    def get_meeting_link(self, obj):
        return get_meeting_page_url(obj, self.context.get("request"))
