from django.urls import path
from .views import (
    MedicalHistoryListCreateView, MedicalHistoryDetailView,
    PrescriptionListCreateView, PrescriptionDetailView,
    MedicalReportListCreateView, MedicalReportDetailView
)

urlpatterns = [
    path('medical-histories/', MedicalHistoryListCreateView.as_view(), name='medical-history-list'),
    path('medical-histories/<int:pk>/', MedicalHistoryDetailView.as_view(), name='medical-history-detail'),

    path('create/', PrescriptionListCreateView.as_view(), name='prescription-list'),
    path('prescriptions/<int:pk>/', PrescriptionDetailView.as_view(), name='prescription-detail'),

    path('medical-report/create/', MedicalReportListCreateView.as_view(), name='medical-report-list'),
    path('medical-reports/<int:pk>/', MedicalReportDetailView.as_view(), name='medical-report-detail'),
]
