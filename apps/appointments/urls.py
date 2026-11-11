from django.urls import path
from .views import (
    AppointmentListCreateView,
    HospitalDetailAPIView,
    HospitalListAPIView,
    dashboard_action,
    hospital_dashboard,
    superadmin_dashboard,
)

urlpatterns = [
    path("", AppointmentListCreateView.as_view(), name="appointment-list"),
    path("appointments/", AppointmentListCreateView.as_view(), name="create-appointment"),
    path("api/appointments/", AppointmentListCreateView.as_view(), name="appointment-calendar"),
    path("hospitals/", HospitalListAPIView.as_view(), name="hospital-list"),
    path("hospitals/<int:pk>/", HospitalDetailAPIView.as_view(), name="hospital-detail"),
    path("hospital-dashboard/", hospital_dashboard, name="hospital-dashboard"),
    path("superadmin-dashboard/", superadmin_dashboard, name="superadmin-dashboard"),
    path("dashboard/actions/<slug:action>/", dashboard_action, name="hospital-dashboard-action"),
]
