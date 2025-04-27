from django.urls import path
from .views import HospitalListAPIView, HospitalDetailAPIView, FullBookingAPIView, HospitalDashboardView

urlpatterns = [
    # Hospital Management URLs
    path('hospitals/', HospitalListAPIView.as_view(), name='hospital-list'),
    path('hospitals/<int:pk>/', HospitalDetailAPIView.as_view(), name='hospital-detail'),
    path('book-appointment/', FullBookingAPIView.as_view(), name='book-appointment'),
    path('hospital-dashboard/', HospitalDashboardView.as_view(), name='hospital-dashboard'),
]

