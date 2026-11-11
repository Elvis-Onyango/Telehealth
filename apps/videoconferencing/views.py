from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.timezone import now
from django.views import View

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.appointments.models import Appointment

from .models import VideoCall
from .serializers import VideoCallSerializer

class VideoCallCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        appointment_id = request.data.get("appointment_id")
        duration = request.data.get("duration", 30)  # Default to 30 mins

        # Validate appointment
        try:
            appointment = Appointment.objects.get(id=appointment_id, type='virtual')
        except Appointment.DoesNotExist:
            return Response({"error": "Virtual appointment not found."}, status=status.HTTP_404_NOT_FOUND)

        if request.user not in (appointment.doctor.user, appointment.patient.user):
            raise PermissionDenied

        if hasattr(appointment, 'video_call'):
            serializer = VideoCallSerializer(
                appointment.video_call,
                context={"request": request},
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Scheduled time
        scheduled_time = timezone.make_aware(
            datetime.combine(appointment.date, appointment.time),
            timezone.get_current_timezone(),
        )

        video_call = VideoCall.objects.create(
            appointment=appointment,
            scheduled_time=scheduled_time,
            duration=duration,
            host=appointment.doctor.user
        )
        video_call.participants.add(appointment.patient.user)

        serializer = VideoCallSerializer(video_call, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CreateMeetFormView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        if not hasattr(request.user, 'role') or request.user.role != 'doctor':
            return Response({"error": "Unauthorized"}, status=403)
        return render(request, 'videoconferencing/create_meeting.html')


class VideoCallListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not hasattr(user, 'role') or user.role != "doctor":
            return Response({"error": "Only doctors can view video calls"}, status=403)

        video_calls = VideoCall.objects.filter(host=user).order_by('-scheduled_time')
        serializer = VideoCallSerializer(video_calls, many=True)
        return Response(serializer.data, status=200)


@login_required
def video_meeting(request, meeting_id):
    meeting = get_object_or_404(VideoCall, meeting_id=meeting_id)

    if request.user != meeting.host and not meeting.participants.filter(id=request.user.id).exists():
        raise PermissionDenied

    if now() < meeting.scheduled_time:
        return redirect(
            "videoconferencing:waiting_room",
            meeting_id=meeting_id,
        )

    meeting_end = meeting.scheduled_time + timedelta(minutes=meeting.duration)
    if now() > meeting_end:
        return render(request, "videoconferencing/meeting_ended.html", {
            'meeting': meeting,
        })

    return render(request, "videoconferencing/meeting.html", {
        "meeting": meeting,
    })


@login_required
def waiting_room(request, meeting_id):
    meeting = get_object_or_404(VideoCall, meeting_id=meeting_id)

    if request.user != meeting.host and not meeting.participants.filter(id=request.user.id).exists():
        raise PermissionDenied

    return render(request, "videoconferencing/waiting.html", {
        "meeting": meeting,
    })
