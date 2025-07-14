from django.urls import path
from .views import HospitalListAPIView, HospitalDetailAPIView, AppointmentCreateView, HospitalDashboardView, AppointmentCalendarAPIView

urlpatterns = [
    # Hospital Management URLs
    path('hospitals/', HospitalListAPIView.as_view(), name='hospital-list'),
    path('hospitals/<int:pk>/', HospitalDetailAPIView.as_view(), name='hospital-detail'),
    path("appointments/", AppointmentCreateView.as_view(), name="create-appointment"),
    path('hospital-dashboard/', HospitalDashboardView.as_view(), name='hospital-dashboard'),
    path('api/appointments/', AppointmentCalendarAPIView.as_view(), name='appointment-calendar')
]

