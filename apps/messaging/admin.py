from django.contrib import admin
from .models import Conversation, Message

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor_name', 'patient_name', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = (
        'doctor__user__first_name', 
        'doctor__user__last_name',
        'patient__user__first_name',
        'patient__user__last_name'
    )
    raw_id_fields = ('doctor', 'patient')
    date_hierarchy = 'created_at'
    
    def doctor_name(self, obj):
        return obj.doctor.user.get_full_name()
    doctor_name.short_description = 'Doctor'
    doctor_name.admin_order_field = 'doctor__user__last_name'
    
    def patient_name(self, obj):
        return obj.patient.user.get_full_name()
    patient_name.short_description = 'Patient'
    patient_name.admin_order_field = 'patient__user__last_name'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'conversation_info', 
        'sender_name', 
        'content_preview', 
        'file_type', 
        'timestamp', 
        'read'
    )
    list_filter = ('read', 'timestamp', 'file_type')
    search_fields = (
        'content',
        'sender__first_name',
        'sender__last_name',
        'conversation__doctor__user__first_name',
        'conversation__doctor__user__last_name',
        'conversation__patient__user__first_name',
        'conversation__patient__user__last_name'
    )
    raw_id_fields = ('conversation', 'sender')
    date_hierarchy = 'timestamp'
    list_select_related = ('conversation', 'sender')
    readonly_fields = ('timestamp',)
    actions = ['mark_as_read', 'mark_as_unread']
    
    def conversation_info(self, obj):
        return f"Dr. {obj.conversation.doctor.user.get_full_name()} ↔ {obj.conversation.patient.user.get_full_name()}"
    conversation_info.short_description = 'Conversation'
    
    def sender_name(self, obj):
        return obj.sender.get_full_name()
    sender_name.short_description = 'Sender'
    sender_name.admin_order_field = 'sender__last_name'
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if obj.content and len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'
    
    def mark_as_read(self, request, queryset):
        queryset.update(read=True)
        self.message_user(request, f"{queryset.count()} messages marked as read")
    mark_as_read.short_description = "Mark selected messages as read"
    
    def mark_as_unread(self, request, queryset):
        queryset.update(read=False)
        self.message_user(request, f"{queryset.count()} messages marked as unread")
    mark_as_unread.short_description = "Mark selected messages as unread"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'conversation__doctor__user',
            'conversation__patient__user',
            'sender'
        )