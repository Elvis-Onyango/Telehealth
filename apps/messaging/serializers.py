from rest_framework import serializers
from .models import Message
from apps.users.models import User


# 👤 Mini user info serializer for display
class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    

# 📥 Message list / detail serializer (read-only)
class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    recipient = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = [
            'id',
            'sender',
            'recipient',
            'message_type',
            'content',
            'file',
            'is_read',
            'timestamp'
        ]


# ✉️ For creating messages
class CreateMessageSerializer(serializers.ModelSerializer):
    recipient = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    message_type = serializers.ChoiceField(choices=Message.MESSAGE_TYPES)

    class Meta:
        model = Message
        fields = ['recipient', 'message_type', 'content', 'file']

    def validate(self, data):
        sender = self.context['request'].user
        recipient = data.get('recipient')

        if sender == recipient:
            raise serializers.ValidationError("You can't message yourself.")

        # If message type is 'file', file must be included
        if data['message_type'] == 'file' and not data.get('file'):
            raise serializers.ValidationError("File message must include a file.")

        # For 'dosage' or 'meeting', content is required
        if data['message_type'] in ['dosage', 'meeting'] and not data.get('content'):
            raise serializers.ValidationError(f"{data['message_type'].capitalize()} message must include content.")

        return data

    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)
