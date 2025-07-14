from rest_framework import serializers
from .models import Hospital, Appointment, Billing
from django.utils import timezone
from datetime import datetime
from django.db import transaction

from rest_framework.exceptions import ValidationError
# ========== Hospital Serializer ==========
class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = '__all__'


# ========== Appointment Serializer ================================================================

from rest_framework import serializers
from .models import Hospital, Appointment, Billing
from django.utils import timezone
from datetime import datetime
from django.db import transaction
from rest_framework.exceptions import ValidationError

class AppointmentCreateSerializer(serializers.ModelSerializer):
    payment_method = serializers.CharField(write_only=True, required=True)
    total_fee = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        write_only=True,
        required=True
    )

    class Meta:
        model = Appointment
        fields = [
            'doctor', 'date', 'time', 'type', 
            'notes', 'reschedule_reason',
            'payment_method', 'total_fee'
        ]

    def validate(self, data):
        # Date validation
        if data['date'] < timezone.now().date():
            raise ValidationError("Appointment date must be in the future")
        
        # Time validation
        appointment_datetime = datetime.combine(data['date'], data['time'])
        appointment_datetime = timezone.make_aware(appointment_datetime)
        
        if appointment_datetime < timezone.now():
            raise ValidationError("Appointment time must be in the future")
        
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not hasattr(request.user, 'patient_profile'):
            raise ValidationError("Only patients can create appointments")

        payment_method = validated_data.pop('payment_method')
        total_fee = validated_data.pop('total_fee')

        # Check for existing appointment
        if Appointment.objects.filter(
            doctor=validated_data['doctor'],
            date=validated_data['date'],
            time=validated_data['time'],
            is_active=True
        ).exists():
            raise ValidationError("Doctor is already booked at this time")

        # Create appointment
        appointment = Appointment.objects.create(
            patient=request.user.patient_profile,
            **validated_data
        )

        # Create billing
        Billing.objects.create(
            appointment=appointment,
            total_fee=total_fee,
            payment_method=payment_method,
            payment_status='pending',
            processed_by=request.user
        )
    def get_video_call_link(self, obj):
        if hasattr(obj, 'video_call'):
            return obj.video_call.meeting_link
        return None
    

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
