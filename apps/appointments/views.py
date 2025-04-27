from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from django.shortcuts import get_object_or_404,render
from .models import Hospital, Appointment, Billing
from .serializers import AppointmentSerializer, BillingSerializer, HospitalSerializer
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


class FullBookingAPIView(APIView):
    """
    Handle the full booking process (appointment + billing) with optional hospital field.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        serializer = AppointmentSerializer(data=request.data, context={'request': request})

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        doctor = get_object_or_404(DoctorProfile, id=data['doctor'])  # Get doctor profile
        
        # Get the hospital from the data (if provided)
        hospital = None
        if 'hospital' in data:
            hospital = get_object_or_404(Hospital, id=data['hospital'])

        # Start transaction to ensure appointment and billing are created together
        try:
            with transaction.atomic():
                # 1. Create the appointment
                appointment = Appointment.objects.create(
                    patient=user.patient_profile,  # Get the patient profile (assuming user has a PatientProfile)
                    doctor=doctor,
                    hospital=hospital,  # Link the hospital to the appointment (if provided)
                    date=data['date'],
                    time=data['time'],
                    notes=data.get('notes', ''),
                    status='confirmed'
                )

                # 2. Create billing for the appointment
                payment_method = data.get('payment_method', 'pending')
                billing = Billing.objects.create(
                    appointment=appointment,
                    total_fee=doctor.consultation_fee,  # Assuming the doctor has a `consultation_fee` attribute
                    paid=False,
                    payment_method=payment_method,
                    payment_status='pending',
                    payment_date=None
                )

                # 3. Simulate the payment process (this part is mock logic)
                payment_success = False
                payment_details = {}

                # Simulating a mock payment process (you can integrate actual payment gateways here)
                if payment_method == 'mpesa':
                    payment_success = True  # Simulate successful payment for Mpesa
                    payment_details = {"transaction_id": "mpesa_12345"}
                elif payment_method == 'card':
                    payment_success = True  # Simulate successful card payment
                    payment_details = {"transaction_id": "card_12345"}

                if not payment_success:
                    raise Exception("Payment failed: " + str(payment_details.get("error", "Unknown error")))

                # 4. Update billing after successful payment
                billing.paid = True
                billing.payment_status = 'paid'
                billing.payment_date = timezone.now()
                billing.save()

                # 5. Return response with the appointment and payment details
                return Response({
                    "message": "Appointment booked and payment successful!",
                    "appointment_id": appointment.id,
                    "transaction": payment_details
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Full booking failed: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#===========================page displays=================================================================================

class HospitalDashboardView(View):
    def get(self, request):
        return render(request, 'appointments/hospital_dashboard.html')

class AppointmentBookingForm(View):
    def get(self,request):
        return render(request,'appointments/appointment_booking.html')
