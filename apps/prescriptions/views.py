from rest_framework import generics, permissions
from .models import MedicalHistory, Prescription, MedicalReport
from .serializers import MedicalHistorySerializer, PrescriptionSerializer, MedicalReportSerializer


class MedicalHistoryListCreateView(generics.ListCreateAPIView):
    """
    View to list all medical histories or create a new one.
    """
    queryset = MedicalHistory.objects.all()
    serializer_class = MedicalHistorySerializer
    permission_classes = [permissions.IsAuthenticated]


class MedicalHistoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View to retrieve, update, or delete a medical history record.
    """
    queryset = MedicalHistory.objects.all()
    serializer_class = MedicalHistorySerializer
    permission_classes = [permissions.IsAuthenticated]


class PrescriptionListCreateView(generics.ListCreateAPIView):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        print("Received data:", request.data)  # Debug log
        return super().create(request, *args, **kwargs)



class PrescriptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View to retrieve, update, or delete a prescription.
    """
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]




class MedicalReportListCreateView(generics.ListCreateAPIView):
    """
    View to list or create medical reports.
    """
    queryset = MedicalReport.objects.all()
    serializer_class = MedicalReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """
        Assigns the authenticated doctor to the report before saving.
        """
        serializer.save(doctor=self.request.user.doctor_profile)




class MedicalReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View to retrieve, update, or delete a medical report.
    """
    queryset = MedicalReport.objects.all()
    serializer_class = MedicalReportSerializer
    permission_classes = [permissions.IsAuthenticated]
