# users/middleware.py
from django.http import HttpResponseForbidden
from django.urls import resolve

class ChatAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Check if this is a chat-related view
        resolved = resolve(request.path_info)
        
        if resolved.url_name in ['thread-list', 'thread-detail', 'message-list']:
            # User must be authenticated and have a verified role
            if not request.user.is_authenticated:
                return HttpResponseForbidden("Access denied")
                
            if not request.user.role in ['doctor', 'patient']:
                return HttpResponseForbidden("Access denied")
                
            # Additional verification checks can be added here
            # For example, check if doctor/patient profile is complete