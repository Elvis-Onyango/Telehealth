from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from django.shortcuts import get_object_or_404,render
from .models import Hospital, Appointment, Billing
from .serializers import AppointmentCreateSerializer, BillingSerializer, HospitalSerializer
from django.db import transaction
from apps.users.models import DoctorProfile, PatientProfile
from django.views import View


# Views for Hospital Management

class HospitalListAPIView(APIView):
    """
    List all hospitals in the system.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        hospitals = Hospital.objects.all()
        serializer = HospitalSerializer(hospitals, many=True)
        return Response(serializer.data)


class HospitalDetailAPIView(APIView):
    """
    Retrieve, update, or delete a hospital's details.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        hospital = get_object_or_404(Hospital, pk=pk)
        serializer = HospitalSerializer(hospital)
        return Response(serializer.data)

    def put(self, request, pk):
        hospital = get_object_or_404(Hospital, pk=pk)
        serializer = HospitalSerializer(hospital, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        hospital = get_object_or_404(Hospital, pk=pk)
        hospital.delete()
        return Response({"message": "Hospital deleted successfully!"}, status=status.HTTP_204_NO_CONTENT)


from rest_framework import generics, permissions
from .models import Appointment
from .serializers import AppointmentCreateSerializer

class AppointmentCreateView(generics.CreateAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Pass the request object in the context instead of trying to save it
        serializer.save()

# views.py
from rest_framework.views import APIView
from rest_framework.response import Response


class AppointmentCalendarAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        appointments = Appointment.objects.filter(
            doctor__user=request.user
        ).select_related('doctor__user', 'patient__user')
        serializer = AppointmentCreateSerializer(appointments, many=True)
        return Response(serializer.data)    
#===========================page displays=================================================================================

class HospitalDashboardView(View):
    def get(self, request):
        return render(request, 'appointments/hospital_dashboard.html')

class AppointmentBookingForm(View):
    def get(self,request):
        return render(request,'appointments/appointment_booking.html')
