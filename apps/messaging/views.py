from pathlib import Path

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework import generics, permissions
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.admin_auth.models import AuditEvent
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.users.models import User

from .access import can_message
from .models import Message
from .serializers import CreateMessageSerializer, MessageSerializer


class MessageContactsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role == "doctor":
            contacts = User.objects.filter(
                Q(patient_profile__assigned_doctors__user=user)
                | Q(patient_profile__appointments__doctor__user=user),
                is_active=True,
            )
        elif user.role == "patient":
            contacts = User.objects.filter(
                Q(doctor_profile__patients__user=user)
                | Q(doctor_profile__appointments__patient__user=user),
                is_active=True,
            )
        else:
            raise PermissionDenied("Only doctors and patients can use messaging.")

        return Response(
            [
                {
                    "id": contact.pk,
                    "name": contact.get_full_name() or contact.username,
                    "role": contact.role,
                }
                for contact in contacts.order_by("first_name", "last_name", "username").distinct()
            ]
        )


class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        contact = get_object_or_404(
            User,
            pk=self.kwargs["contact_id"],
            is_active=True,
        )
        if not can_message(user, contact):
            raise PermissionDenied("You are not allowed to view this conversation.")

        return Message.objects.filter(
            Q(sender=user, recipient=contact)
            | Q(sender=contact, recipient=user)
        ).select_related("sender", "recipient").order_by("timestamp", "pk")


class SendMessageView(generics.CreateAPIView):
    serializer_class = CreateMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def perform_create(self, serializer):
        sender = self.request.user
        recipient = serializer.validated_data["recipient"]
        if not can_message(sender, recipient):
            raise PermissionDenied("You are not allowed to message this user.")

        message = serializer.save(sender=sender)
        first_id, second_id = sorted((sender.pk, recipient.pk))
        async_to_sync(get_channel_layer().group_send)(
            f"chat_{first_id}_{second_id}",
            {
                "type": "chat.message",
                "message": MessageSerializer(
                    message,
                    context={"request": self.request},
                ).data,
            },
        )


class MessageAttachmentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, message_id):
        message = get_object_or_404(
            Message.objects.select_related("sender", "recipient"),
            pk=message_id,
        )
        if not request.user.is_superuser and request.user not in (
            message.sender,
            message.recipient,
        ):
            raise PermissionDenied("You are not allowed to access this attachment.")
        elif not request.user.is_superuser:
            contact = message.recipient if request.user == message.sender else message.sender
            if not can_message(request.user, contact):
                raise PermissionDenied("You are not allowed to access this attachment.")
        if not message.file:
            raise NotFound("This message has no attachment.")
        if request.user.is_superuser:
            AuditEvent.objects.create(
                actor=request.user,
                action="downloaded_message_attachment",
                object_type="message",
                object_id=str(message.pk),
            )

        filename = Path(message.file.name).name
        return FileResponse(
            message.file.open("rb"),
            as_attachment=True,
            filename=filename,
        )


@method_decorator(login_required(login_url="/api/users/login-page/"), name="dispatch")
class ChatTemplateView(View):
    def get(self, request):
        user = request.user

        if user.role not in ["doctor", "patient"]:
            return redirect(reverse("users:login-page") + f"?next={request.path}")

        if user.role == "doctor" and not hasattr(user, "doctor_profile"):
            return redirect(reverse("users:doctor-profile-create"))

        if user.role == "patient" and not hasattr(user, "patient_profile"):
            return redirect(reverse("users:patient-profile-create"))

        return render(
            request,
            "messaging/chat.html",
            {
                "chat_context": {
                    "role": user.role,
                    "username": user.username,
                    "user_id": user.id,
                }
            },
        )
