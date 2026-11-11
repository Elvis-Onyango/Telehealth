from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone
from rest_framework import serializers

from .models import Appointment, Billing, Hospital


class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = "__all__"


class AppointmentCreateSerializer(serializers.ModelSerializer):
    patient = serializers.IntegerField(source="patient_id", read_only=True)
    patient_name = serializers.CharField(
        source="patient.user.get_full_name",
        read_only=True,
    )
    doctor_name = serializers.CharField(
        source="doctor.user.get_full_name",
        read_only=True,
    )
    consultation_fee = serializers.DecimalField(
        source="doctor.consultation_fee",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    payment_method = serializers.ChoiceField(
        choices=Billing.PAYMENT_METHODS,
        write_only=True,
    )
    payment_status = serializers.SerializerMethodField()
    video_call_link = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        validators = []
        fields = [
            "id",
            "patient",
            "patient_name",
            "doctor",
            "doctor_name",
            "date",
            "time",
            "status",
            "type",
            "notes",
            "consultation_fee",
            "payment_method",
            "payment_status",
            "video_call_link",
        ]
        read_only_fields = ["id", "patient", "status"]

    def validate(self, attrs):
        appointment_date = attrs["date"]
        appointment_time = attrs["time"]
        doctor = attrs["doctor"]
        appointment_datetime = timezone.make_aware(
            datetime.combine(appointment_date, appointment_time),
            timezone.get_current_timezone(),
        )

        if appointment_datetime <= timezone.now():
            raise serializers.ValidationError(
                {"date": "Appointment date and time must be in the future."}
            )

        if doctor.consultation_fee < 0:
            raise serializers.ValidationError(
                {"doctor": "This doctor's consultation fee is invalid."}
            )

        weekday = appointment_date.strftime("%A").lower()
        available_days = set(doctor.available_days.values_list("day", flat=True))
        if available_days and weekday not in available_days:
            raise serializers.ValidationError(
                {"date": "This doctor is not available on the selected day."}
            )

        availability = doctor.availabilities.filter(day=weekday)
        if doctor.availabilities.exists():
            if not availability.filter(
                start_time__lte=appointment_time,
                end_time__gt=appointment_time,
            ).exists():
                raise serializers.ValidationError(
                    {"time": "This doctor is not available at the selected time."}
                )

        if Appointment.objects.filter(
            doctor=doctor,
            date=appointment_date,
            time=appointment_time,
            is_active=True,
        ).exists():
            raise serializers.ValidationError(
                {"time": "This doctor is already booked at the selected time."}
            )

        request = self.context.get("request")
        if not request or not hasattr(request.user, "patient_profile"):
            raise serializers.ValidationError(
                {"patient": "Complete your patient profile before booking."}
            )

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        payment_method = validated_data.pop("payment_method")
        doctor = validated_data["doctor"]

        try:
            with transaction.atomic():
                appointment = Appointment.objects.create(
                    patient=request.user.patient_profile,
                    hospital=doctor.hospital,
                    **validated_data,
                )
                Billing.objects.create(
                    appointment=appointment,
                    total_fee=doctor.consultation_fee,
                    payment_method=payment_method,
                    payment_status="pending",
                    processed_by=request.user,
                )
                doctor.patients.add(appointment.patient)
        except IntegrityError as error:
            if Appointment.objects.filter(
                doctor=doctor,
                date=validated_data["date"],
                time=validated_data["time"],
                is_active=True,
            ).exists():
                raise serializers.ValidationError(
                    {"time": "This doctor is already booked at the selected time."}
                ) from error
            raise

        return appointment

    def get_payment_status(self, obj):
        try:
            return obj.billing.payment_status
        except Billing.DoesNotExist:
            return None

    def get_video_call_link(self, obj):
        try:
            meeting_url = reverse(
                "videoconferencing:video_meeting",
                kwargs={"meeting_id": obj.video_call.meeting_id},
            )
        except ObjectDoesNotExist:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(meeting_url) if request else meeting_url
