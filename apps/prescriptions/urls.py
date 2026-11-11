from django.urls import path
from .views import (
    MedicalHistoryListCreateView, MedicalHistoryDetailView,
    PrescriptionListCreateView, PrescriptionDetailView,
    MedicalReportListCreateView, MedicalReportDetailView, MedicalReportDownloadView,
    VisitSummaryDownloadView, medical_report_create_page, symptom_intake_page,
)

urlpatterns = [
    path('medical-histories/', MedicalHistoryListCreateView.as_view(), name='medical-history-list'),
    path('medical-histories/<int:pk>/', MedicalHistoryDetailView.as_view(), name='medical-history-detail'),

    path('create/', PrescriptionListCreateView.as_view(), name='prescription-list'),
    path('prescriptions/<int:pk>/', PrescriptionDetailView.as_view(), name='prescription-detail'),

    path('medical-report/create/', MedicalReportListCreateView.as_view(), name='medical-report-list'),
    path('medical-report/new/', medical_report_create_page, name='medical-report-create-page'),
    path('medical-reports/<int:pk>/file/', MedicalReportDownloadView.as_view(), name='medical-report-download'),
    path('medical-reports/<int:pk>/', MedicalReportDetailView.as_view(), name='medical-report-detail'),
    path('appointments/<int:appointment_id>/symptom-intake/', symptom_intake_page, name='symptom-intake-page'),
    path('appointments/<int:appointment_id>/summary/', VisitSummaryDownloadView.as_view(), name='visit-summary-download'),
]
