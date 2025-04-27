from django.contrib import admin
from .models import VideoCall

class VideoCallAdmin(admin.ModelAdmin):
    list_display = ('host', 'scheduled_time', 'duration', 'meeting_link')
    list_filter = ('scheduled_time',)
    search_fields = ('host__username', 'meeting_id')

admin.site.register(VideoCall, VideoCallAdmin)
