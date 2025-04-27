from django.urls import path
from .views import video_meeting, waiting_room, VideoCallCreateView, CreateMeetFormView, VideoCallListView
app_name = 'videoconferencing'
urlpatterns = [
    path("meeting/<str:meeting_id>/", video_meeting, name="video_meeting"),
    path("waiting/<str:meeting_id>/", waiting_room, name="waiting_room"),
    path("create-form/", CreateMeetFormView.as_view(), name="create-form"),
    path("create-calls/", VideoCallCreateView.as_view(), name="video_call_create"),
    path('video-calls/', VideoCallListView.as_view(), name='video-call-list'),
]

