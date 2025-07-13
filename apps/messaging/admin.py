from django.contrib import admin
from .models import Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'message_type', 'timestamp', 'is_read']
    list_filter = ['message_type', 'timestamp', 'is_read']
    search_fields = ['content', 'sender__username', 'recipient__username']
