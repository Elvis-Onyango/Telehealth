from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from apps.users.models import DoctorProfile, PatientProfile
import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from datetime import datetime
from django.views import View
from django.shortcuts import render

class ConversationListView(generics.ListAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'doctor':
            doctor_profile = get_object_or_404(DoctorProfile, user=user)
            return Conversation.objects.filter(doctor=doctor_profile)
        elif user.role == 'patient':
            patient_profile = get_object_or_404(PatientProfile, user=user)
            return Conversation.objects.filter(patient=patient_profile)
        return Conversation.objects.none()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class StartConversationView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        other_user_id = request.data.get('user_id')
        
        if user.role == 'doctor':
            doctor_profile = get_object_or_404(DoctorProfile, user=user)
            patient_profile = get_object_or_404(PatientProfile, user__id=other_user_id)
            conversation, created = Conversation.objects.get_or_create(
                doctor=doctor_profile,
                patient=patient_profile
            )
        elif user.role == 'patient':
            patient_profile = get_object_or_404(PatientProfile, user=user)
            doctor_profile = get_object_or_404(DoctorProfile, user__id=other_user_id)
            conversation, created = Conversation.objects.get_or_create(
                doctor=doctor_profile,
                patient=patient_profile
            )
        else:
            return Response({'error': 'Invalid user role'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ConversationSerializer(conversation, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']
        user = self.request.user
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        # Verify user is part of this conversation
        if user.role == 'doctor' and conversation.doctor.user != user:
            return Message.objects.none()
        elif user.role == 'patient' and conversation.patient.user != user:
            return Message.objects.none()
            
        return Message.objects.filter(conversation=conversation).order_by('timestamp')

class MarkMessagesAsReadView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, conversation_id):
        user = request.user
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        # Verify user is part of this conversation
        if (user.role == 'doctor' and conversation.doctor.user != user) or \
           (user.role == 'patient' and conversation.patient.user != user):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        # Mark all unread messages as read
        Message.objects.filter(
            conversation=conversation,
            read=False
        ).exclude(
            sender=user
        ).update(read=True)
        
        return Response({'status': 'messages marked as read'}, status=status.HTTP_200_OK)

class FileUploadView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES['file']
        if file.size > 10 * 1024 * 1024:  # 10MB limit
            return Response({'error': 'File too large (max 10MB)'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create a unique filename
        ext = os.path.splitext(file.name)[1]
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"chat_uploads/{request.user.id}_{timestamp}{ext}"
        
        # Save the file
        path = default_storage.save(filename, ContentFile(file.read()))
        file_url = default_storage.url(path)
        
        # Determine file type
        if file.content_type.startswith('image/'):
            file_type = 'image'
        elif file.content_type == 'application/pdf':
            file_type = 'pdf'
        elif 'wordprocessingml' in file.content_type or 'msword' in file.content_type:
            file_type = 'document'
        else:
            file_type = 'file'
        
        return Response({
            'url': request.build_absolute_uri(file_url),
            'file_type': file_type
        }, status=status.HTTP_201_CREATED)


class ChatPage(View):
    def get(self):
        return render(request,'messaging/chat.html') 
