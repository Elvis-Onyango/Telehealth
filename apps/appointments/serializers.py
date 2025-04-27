from rest_framework import serializers
from .models import Hospital, Appointment, Billing
from django.utils import timezone

# Hospital Serializer
class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = '__all__'


# Appointment Serializer
class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.user.get_full_name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.user.get_full_name", read_only=True)
    hospital_name = serializers.CharField(source="hospital.name", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'patient_name', 'doctor', 'doctor_name',
            'hospital', 'hospital_name', 'date', 'time', 'status', 'notes', 
            'reschedule_reason', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'patient', 'patient_name', 'created_at', 'updated_at']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['patient'] = user.patient_profile
        # Create the Appointment
        appointment = super().create(validated_data)
        
        # After the Appointment is created, create the Billing automatically
        # Assuming `payment_method` is passed in the request and passed to the `create` method
        payment_method = validated_data.get('payment_method', 'pending')  # Default to 'pending' if not provided
        
        Billing.objects.create(
            appointment=appointment,
            total_fee=appointment.doctor.consultation_fee,  # Assuming doctor has a `consultation_fee` field
            paid=False,
            payment_method=payment_method,  # Use the payment method passed during appointment creation
            payment_status='pending',
            payment_date=None  # Set to None initially, as payment isn't done yet
        )

        return appointment


# Billing Serializer
class BillingSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="appointment.patient.user.get_full_name", read_only=True)
    doctor_name = serializers.CharField(source="appointment.doctor.user.get_full_name", read_only=True)
    appointment_date = serializers.DateField(source="appointment.date", read_only=True)

    class Meta:
        model = Billing
        fields = [
            'id', 'appointment', 'patient_name', 'doctor_name', 'appointment_date', 
            'total_fee', 'paid', 'payment_method', 'payment_status', 'payment_date'
        ]
        read_only_fields = ['id', 'appointment', 'patient_name', 'doctor_name', 'appointment_date']

    def update(self, instance, validated_data):
        """Override update to handle payment updates."""
        instance.paid = validated_data.get('paid', instance.paid)
        instance.payment_method = validated_data.get('payment_method', instance.payment_method)
        instance.payment_status = validated_data.get('payment_status', instance.payment_status)
        if instance.paid and not instance.payment_date:
            instance.payment_date = timezone.now()  # Set payment date when paid
        instance.save()
        return instance
