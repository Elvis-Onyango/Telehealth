from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View

from .models import Message
from .serializers import MessageSerializer, CreateMessageSerializer
from apps.users.models import User, DoctorProfile, PatientProfile
from django.shortcuts import redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse

class MessageListView(generics.ListAPIView):
    """
    API View to fetch all messages between a logged-in user and a contact.
    Only accessible if there's a valid doctor-patient relationship.
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        contact_id = self.kwargs['contact_id']
        contact = User.objects.get(pk=contact_id)

        if user.role == 'doctor':
            if not hasattr(user, 'doctor_profile'):
                raise PermissionDenied("Doctor profile not found.")
            if not user.doctor_profile.patients.filter(user=contact).exists():
                raise PermissionDenied("This patient is not assigned to you.")

        elif user.role == 'patient':
            if not hasattr(user, 'patient_profile'):
                raise PermissionDenied("Patient profile not found.")
            if not hasattr(contact, 'doctor_profile') or not contact.doctor_profile.patients.filter(user=user).exists():
                raise PermissionDenied("This doctor is not treating you.")
        else:
            raise PermissionDenied("Invalid role.")

        return Message.objects.filter(
            Q(sender=user, recipient=contact) |
            Q(sender=contact, recipient=user)
        ).order_by('timestamp')


from rest_framework.exceptions import PermissionDenied
from django.core.exceptions import ObjectDoesNotExist

class SendMessageView(generics.CreateAPIView):
    serializer_class = CreateMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        sender = self.request.user
        recipient = serializer.validated_data['recipient']

        if sender == recipient:
            raise PermissionDenied("You can't message yourself.")

        if sender.role == 'doctor':
            try:
                doctor_profile = sender.doctor_profile
                patient_profile = recipient.patient_profile
            except ObjectDoesNotExist:
                raise PermissionDenied("Profile not found.")

            #  filter by recipient.user.id (doctor_profile.patients is M2M of PatientProfile)
            if not doctor_profile.patients.filter(user=recipient).exists():
                raise PermissionDenied("You are not assigned to this patient.")

        elif sender.role == 'patient':
            try:
                patient_profile = sender.patient_profile
                doctor_profile = recipient.doctor_profile
            except ObjectDoesNotExist:
                raise PermissionDenied("Profile not found.")

            #  filter by recipient.user.id (patient_profile.doctors is M2M of DoctorProfile)
            if not patient_profile.doctors.filter(user=recipient).exists():
                raise PermissionDenied("You are not assigned to this doctor.")

        else:
            raise PermissionDenied("Unauthorized role.")

        serializer.save(sender=sender)







@method_decorator(login_required(login_url="/api/users/login-page/"), name='dispatch')
class ChatTemplateView(View):
    def get(self, request):
        user = request.user

        # Redirect if user role is not doctor or patient
        if user.role not in ['doctor', 'patient']:
            return redirect(reverse('users:login-page') + f'?next={request.path}')

        # Redirect if profile is missing
        if user.role == 'doctor' and not hasattr(user, 'doctor_profile'):
            return redirect(reverse('users:doctor-profile-create'))

        if user.role == 'patient' and not hasattr(user, 'patient_profile'):
            return redirect(reverse('users:patient-profile-create'))

        # If all is good, show chat UI
        context = {
            'role': user.role,
            'username': user.username,
            'user_id': user.id,
        }
        return render(request, 'messaging/chat.html', context)


