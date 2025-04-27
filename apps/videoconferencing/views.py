from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import generics, permissions
from datetime import datetime
from django.utils.timezone import now
from .models import VideoCall
from .serializers import VideoCallSerializer
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import VideoCall
from .serializers import VideoCallSerializer
from rest_framework.permissions import IsAuthenticated
from apps.appointments.models import Appointment
from django.core.mail import send_mail
from django.conf import settings


from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import VideoCall
from .serializers import VideoCallSerializer
import uuid

User = get_user_model()  # Get the custom User model

class VideoCallCreateView(APIView):
    authentication_classes = []  # No authentication
    permission_classes = []  # Anyone can access

    def post(self, request):
        # Generate a unique meeting ID
        meeting_id = str(uuid.uuid4())
        meeting_link = f"https://meet.jit.si/{meeting_id}"

        # Get data from request
        scheduled_time = request.data.get("scheduled_time")
        duration = request.data.get("duration")

        #Assign the first user from the custom User model
        default_host = User.objects.first()  
        if not default_host:
            return Response({"error": "No users exist. Create at least one user."}, status=status.HTTP_400_BAD_REQUEST)

        # Create the meeting with the default host
        video_call = VideoCall.objects.create(
            meeting_id=meeting_id,
            meeting_link=meeting_link,
            scheduled_time=scheduled_time,
            duration=duration,
            host=default_host  # Assign the default host
        )

        serializer = VideoCallSerializer(video_call)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CreateMeetFormView(View):
    def get(self, request):
        return render(request,'videoconferencing/create_meeting.html')



class VideoCallListView(APIView):
    """Fetch all video calls hosted by the logged-in doctor"""
    permission_classes = [IsAuthenticated]  # Requires a valid token

    def get(self, request):
        user = request.user

        # Ensure only doctors can access this view
        if user.role != "doctor":
            return Response({"error": "Only doctors can view video calls"}, status=status.HTTP_403_FORBIDDEN)

        # Fetch video calls hosted by the logged-in doctor
        video_calls = VideoCall.objects.filter(host=user)
        serializer = VideoCallSerializer(video_calls, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)




# View to render the meeting page
def video_meeting(request, meeting_id):
    meeting = get_object_or_404(VideoCall, meeting_id=meeting_id)
    
    # Check if the meeting time has arrived
    if meeting.start_time > now():  # Assuming start_time is a DateTimeField
        return redirect("waiting_room", meeting_id=meeting_id)

    return render(request, "videoconferencing/meeting.html", {"meeting": meeting})

# View to render the waiting page
def waiting_room(request, meeting_id):
    meeting = get_object_or_404(VideoCall, meeting_id=meeting_id)
    return render(request, "videoconferencing/waiting.html", {"meeting": meeting})
