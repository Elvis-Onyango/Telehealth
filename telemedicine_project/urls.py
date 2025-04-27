from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views

# Admin site customization
admin.site.site_header = "Telemedicine Admin"
admin.site.site_title = "Telemedicine Dashboard"
admin.site.index_title = "Welcome to Telemedicine Admin Panel"




urlpatterns = [
    # Admin panel

    path("admin/logout/", auth_views.LogoutView.as_view(next_page="/admin-login/"), name="logout"),
    path('admin/',admin.site.urls),
    path("admin-login/", include("apps.admin_auth.urls")),  # Custom admin login
   
    # API routes
    path('api/users/', include('apps.users.urls')),  # Custom user authentication APIs
    path('api/appointments/', include('apps.appointments.urls')),
    path('api/prescriptions/', include('apps.prescriptions.urls')),
    path('api/messaging/', include('apps.messaging.urls')),
    path('api/videoconferencing/', include('apps.videoconferencing.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/pharmacy/', include('apps.pharmacy.urls')),

    # Landing page routes
    path('', include('apps.landing.urls')),
]
# Redirect the default admin login to our custom login page
admin.site.login = lambda request: redirect("/admin-login/")

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)