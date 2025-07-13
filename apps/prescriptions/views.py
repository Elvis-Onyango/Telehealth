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


from rest_framework.exceptions import PermissionDenied

class PrescriptionListCreateView(generics.ListCreateAPIView):
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'patient_profile'):
            return Prescription.objects.filter(patient__user=user)
        elif hasattr(user, 'doctor_profile'):
            return Prescription.objects.filter(doctor__user=user)
        return Prescription.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'doctor_profile'):
            serializer.save(doctor=user.doctor_profile)
        elif hasattr(user, 'patient_profile'):
            serializer.save(patient=user.patient_profile)
        else:
            raise PermissionDenied("User must be a doctor or patient.")





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
