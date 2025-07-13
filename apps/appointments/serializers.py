from rest_framework import serializers
from .models import Hospital, Appointment, Billing
from django.utils import timezone
from datetime import datetime
from django.db import transaction

# ========== Hospital Serializer ==========
class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = '__all__'


# ========== Appointment Serializer ==========
from rest_framework import serializers
from .models import Appointment, Billing
from django.utils import timezone

class AppointmentCreateSerializer(serializers.ModelSerializer):
    payment_method = serializers.CharField(write_only=True)
    total_fee = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True)

    class Meta:
        model = Appointment
        fields = ['doctor', 'date', 'time', 'type', 'notes', 'reschedule_reason', 'payment_method', 'total_fee']
    @transaction.atomic
    def create(self, validated_data):
        request = self.context['request']
        patient = request.user.patient_profile  # assumes logged-in user has patient_profile

        payment_method = validated_data.pop('payment_method')
        total_fee = validated_data.pop('total_fee')

        # Create appointment
        appointment = Appointment.objects.create(patient=patient, **validated_data)

        # Create billing
        Billing.objects.create(
            appointment=appointment,
            total_fee=total_fee,
            payment_method=payment_method,
            payment_status='paid',
            payment_date=timezone.now(),
            processed_by=request.user
        )

        return appointment



class BillingSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="appointment.patient.user.get_full_name", read_only=True)
    doctor_name = serializers.CharField(source="appointment.doctor.user.get_full_name", read_only=True)
    appointment_date = serializers.DateField(source="appointment.date", read_only=True)

    class Meta:
        model = Billing
        fields = [
            'id', 'appointment', 'patient_name', 'doctor_name', 'appointment_date',
            'total_fee', 'payment_method', 'payment_status', 'payment_date'
        ]
        read_only_fields = ['id', 'appointment', 'patient_name', 'doctor_name', 'appointment_date', 'total_fee']

    def update(self, instance, validated_data):
        instance.payment_method = validated_data.get('payment_method', instance.payment_method)
        instance.payment_status = validated_data.get('payment_status', instance.payment_status)

        if instance.payment_status == 'paid' and not instance.payment_date:
            instance.payment_date = timezone.now()

        instance.save()
        return instance
