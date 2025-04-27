from rest_framework import serializers
from .models import Conversation, Message
from apps.users.models import User

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    sender_id = serializers.IntegerField(source='sender.id', read_only=True)
    is_doctor = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'sender_id', 'sender_name', 'is_doctor', 
                 'content', 'file', 'file_type', 'timestamp', 'read']

    def get_is_doctor(self, obj):
        return getattr(obj.sender, 'role', '') == 'doctor'

class ConversationSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.user.get_full_name', read_only=True)
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.IntegerField(read_only=True)  # Optimized

    class Meta:
        model = Conversation
        fields = ['id', 'doctor', 'patient', 'doctor_name', 'patient_name', 
                 'created_at', 'updated_at', 'last_message', 'unread_count']

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-timestamp').first()
        return MessageSerializer(last_msg).data if last_msg else None
