from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views
from django.db.models import Sum

from apps.admin_auth.views import CustomAdminLoginView
from apps.appointments.models import Appointment, Billing, Hospital
from apps.users.models import User

# Admin site customization
admin.site.site_header = "Telemedicine Admin"
admin.site.site_title = "Telemedicine Dashboard"
admin.site.index_title = "Welcome to Telemedicine Admin Panel"
admin.site.index_template = "admin/index.html"


def _superadmin_dashboard_stats():
    return {
        "users": User.objects.count(),
        "appointments": Appointment.objects.count(),
        "billing_paid_total": Billing.objects.filter(
            payment_status="paid"
        ).aggregate(total=Sum("total_fee"))["total"] or 0,
        "hospitals": Hospital.objects.count(),
    }


_original_each_context = admin.site.each_context


def _custom_each_context(request):
    context = _original_each_context(request)
    if request.user.is_authenticated and request.user.is_superuser:
        context["admin_dashboard_stats"] = _superadmin_dashboard_stats()
    return context


admin.site.each_context = _custom_each_context


urlpatterns = [
    # Admin panel
    path(
        "admin/logout/",
        auth_views.LogoutView.as_view(next_page="/admin-login/"),
        name="logout",
    ),
    path("admin/", admin.site.urls),
    path("admin-login/", include("apps.admin_auth.urls")),
    path("hospital-login/", CustomAdminLoginView.as_view(), name="hospital-login"),

    # API routes
    path("api/users/", include("apps.users.urls")),
    path("api/appointments/", include("apps.appointments.urls")),
    path("api/prescriptions/", include("apps.prescriptions.urls")),
    path("api/messaging/", include("apps.messaging.urls")),
    path("api/videoconferencing/", include("apps.videoconferencing.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/pharmacy/", include("apps.pharmacy.urls")),

    # Landing page routes
    path("", include("apps.landing.urls")),
]

# Redirect the default admin login to our custom login page
admin.site.login = lambda request: redirect("/admin-login/")

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
