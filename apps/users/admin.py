from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, DoctorProfile, PatientProfile, Weekday, DoctorAvailability
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe


# =================== Custom User Admin ===================
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'phone', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'phone', 'first_name', 'last_name')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'address', 'gender', 'profile_picture')}),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'role',
                'groups',
                'user_permissions',
            )
        }),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

admin.site.register(User, CustomUserAdmin)


@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("doctor", "day", "start_time", "end_time")
    list_filter = ("day",)
    search_fields = ("doctor__user__username", "doctor__user__last_name")


# =================== Weekday Admin ===================
@admin.register(Weekday)
class WeekdayAdmin(admin.ModelAdmin):
    list_display = ('day',)
    search_fields = ('day',)


# =================== Doctor Profile Admin ===================
@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'hospital', 'consultation_fee', 'years_of_experience', 'get_patients', 'get_available_days')
    search_fields = ('user__username', 'specialization', 'hospital__name')
    list_filter = ('specialization', 'years_of_experience', 'available_days')

    def get_patients(self, obj):
        return ", ".join([patient.user.username for patient in obj.patients.all()])
    
    get_patients.short_description = "Patients"

    def get_available_days(self, obj):
        return ", ".join([day.day.capitalize() for day in obj.available_days.all()])
    
    get_available_days.short_description = "Available Days"


# =================== Patient Profile Admin ===================
@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_of_birth', 'gender', 'blood_type', 'get_primary_doctor')
    search_fields = ('user__username', 'blood_type', 'user__first_name', 'user__last_name')
    list_filter = ('blood_type', 'gender', 'primary_doctor')

    def get_primary_doctor(self, obj):
        return obj.primary_doctor.user.username if obj.primary_doctor else "No Doctor Assigned"
    
    get_primary_doctor.short_description = "Primary Doctor"


#=======================messaging===============================================


class MessageAdmin(admin.ModelAdmin):
    list_display = (
        'message_preview',
        'sender_link',
        'recipient_link',
        'message_type_icon',
        'timestamp',
        'is_read_status',
        'attachments'
    )
    list_filter = (
        'message_type',
        'is_read',
        'timestamp',
        ('sender', admin.RelatedOnlyFieldListFilter),
        ('recipient', admin.RelatedOnlyFieldListFilter),
    )
    search_fields = (
        'content',
        'sender__first_name',
        'sender__last_name',
        'recipient__first_name',
        'recipient__last_name'
    )
    readonly_fields = (
        'timestamp',
        'message_type',
        'sender_link',
        'recipient_link',
        'content_preview',
        'attachment_preview'
    )
    fieldsets = (
        ('Message Information', {
            'fields': (
                'sender_link',
                'recipient_link',
                'timestamp',
                'is_read',
                'message_type'
            )
        }),
        ('Content', {
            'fields': (
                'content_preview',
                'attachment_preview'
            )
        }),
    )
    actions = ['mark_as_read', 'mark_as_unread']
    date_hierarchy = 'timestamp'
    list_per_page = 20
    list_select_related = ('sender', 'recipient')

    def message_preview(self, obj):
        preview = obj.content[:50] + '...' if obj.content else '[No text content]'
        return format_html(
            '<span title="{}">{}</span>',
            obj.content if obj.content else '',
            preview
        )
    message_preview.short_description = 'Message Preview'

    def sender_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.sender.id])
        return format_html(
            '<a href="{}">{} {}</a>',
            url,
            obj.sender.first_name,
            obj.sender.last_name
        )
    sender_link.short_description = 'Sender'
    sender_link.admin_order_field = 'sender'

    def recipient_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.recipient.id])
        return format_html(
            '<a href="{}">{} {}</a>',
            url,
            obj.recipient.first_name,
            obj.recipient.last_name
        )
    recipient_link.short_description = 'Recipient'
    recipient_link.admin_order_field = 'recipient'

    def message_type_icon(self, obj):
        icons = {
            'text': 'fa-comment',
            'image': 'fa-image',
            'video': 'fa-video',
            'file': 'fa-file',
            'link': 'fa-link'
        }
        return format_html(
            '<i class="fas {}" title="{}"></i>',
            icons.get(obj.message_type, 'fa-question'),
            obj.get_message_type_display()
        )
    message_type_icon.short_description = 'Type'

    def is_read_status(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if obj.is_read else 'red',
            '✓ Read' if obj.is_read else '✗ Unread'
        )
    is_read_status.short_description = 'Status'
    is_read_status.admin_order_field = 'is_read'

    def attachments(self, obj):
        links = []
        if obj.file:
            links.append(format_html(
                '<a href="{}" target="_blank"><i class="fas fa-file"></i> File</a>',
                obj.file.url
            ))
        if obj.video:
            links.append(format_html(
                '<a href="{}" target="_blank"><i class="fas fa-video"></i> Video</a>',
                obj.video.url
            ))
        if obj.link:
            links.append(format_html(
                '<a href="{}" target="_blank"><i class="fas fa-link"></i> Link</a>',
                obj.link
            ))
        return mark_safe(' '.join(links)) if links else '-'
    attachments.short_description = 'Attachments'

    def content_preview(self, obj):
        if not obj.content:
            return '-'
        return format_html(
            '<div style="background: #f8f8f8; padding: 10px; border-radius: 5px; white-space: pre-wrap;">{}</div>',
            obj.content
        )
    content_preview.short_description = 'Full Content'

    def attachment_preview(self, obj):
        previews = []
        if obj.file:
            if obj.message_type == 'image':
                previews.append(format_html(
                    '<div style="margin-bottom: 10px;">'
                    '<h4>Image Attachment</h4>'
                    '<img src="{}" style="max-width: 300px; max-height: 300px; border: 1px solid #ddd;">'
                    '</div>',
                    obj.file.url
                ))
            else:
                previews.append(format_html(
                    '<div style="margin-bottom: 10px;">'
                    '<h4>File Attachment</h4>'
                    '<a href="{}" target="_blank">Download File</a>'
                    '</div>',
                    obj.file.url
                ))
        
        if obj.video:
            previews.append(format_html(
                '<div style="margin-bottom: 10px;">'
                '<h4>Video Attachment</h4>'
                '<video controls style="max-width: 300px; max-height: 300px; border: 1px solid #ddd;">'
                '<source src="{}" type="video/mp4">'
                'Your browser does not support the video tag.'
                '</video>'
                '</div>',
                obj.video.url
            ))
        
        if obj.link:
            previews.append(format_html(
                '<div style="margin-bottom: 10px;">'
                '<h4>Link</h4>'
                '<a href="{}" target="_blank">{}</a>'
                '</div>',
                obj.link, obj.link
            ))
        
        return mark_safe(''.join(previews)) if previews else '-'
    attachment_preview.short_description = 'Attachment Previews'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('sender', 'recipient')

    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} messages marked as read.')
    mark_as_read.short_description = 'Mark selected messages as read'

    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} messages marked as unread.')
    mark_as_unread.short_description = 'Mark selected messages as unread'

    class Media:
        css = {
            'all': [
                'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css',
                'css/admin-message.css'
            ]
        }