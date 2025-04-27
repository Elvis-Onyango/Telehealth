from rest_framework import serializers
from .models import  VideoCall

class VideoCallSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoCall
        fields = '__all__'
        read_only_fields = ['meeting_id', 'meeting_link']  # Prevent manual editing

