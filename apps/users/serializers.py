from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, DoctorProfile, PatientProfile, Weekday, DoctorAvailability 
from apps.appointments.serializers import HospitalSerializer
from datetime import datetime, timedelta
from apps.prescriptions.serializers import MedicalHistorySerializer, MedicalReportSerializer


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'address', 'gender', 'role', 'profile_picture']

class SimpleUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()



class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorAvailability
        fields = ['id', 'day', 'start_time', 'end_time']


class WeekdaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Weekday
        fields = ['id','day']


class DoctorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # Fetch full user details
    available_days = WeekdaySerializer(many=True, read_only=True)  # Fetch full weekday names
    hospital = HospitalSerializer(read_only = True)
    availabilities = DoctorAvailabilitySerializer(many=True, read_only=True)
    today_slots = serializers.SerializerMethodField()

    class Meta:
        model = DoctorProfile
        fields = [
            'id', 'user', 'specialization', 'hospital', 'available_days',
            'consultation_fee', 'years_of_experience', 'license_number',
            'certifications', 'profile_picture','availabilities','today_slots'
        ]

    def create(self, validated_data):
        """Create a doctor profile"""
        available_days = validated_data.pop('available_days', [])
        doctor_profile = DoctorProfile.objects.create(**validated_data)
        doctor_profile.available_days.set(available_days)
        return doctor_profile



    def get_today_slots(self, obj):
        """
        Return available time slots for today.
        """
        today_day = datetime.today().strftime("%A")
        now = datetime.now().time()

        # Get availability entries for today
        today_availabilities = obj.availabilities.filter(day=today_day)

        slots = []

        for avail in today_availabilities:
            start = datetime.combine(datetime.today(), avail.start_time)
            end = datetime.combine(datetime.today(), avail.end_time)

            while start + timedelta(minutes=30) <= end:
                time_str = start.strftime('%H:%M')
                if start.time() > now:
                    slots.append(time_str)
                start += timedelta(minutes=30)

        return slots


class PatientProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # Fetch full user details
    medical_history = MedicalHistorySerializer(read_only=True)  
    current_medications = MedicalReportSerializer(many=True, read_only=True)  
    doctors = serializers.SerializerMethodField()

    class Meta:
        model = PatientProfile
        fields = [
            'id', 'user', 'date_of_birth', 'gender', 'blood_type',
            'medical_history', 'current_medications', 'emergency_contact_name',
            'emergency_contact_phone', 'profile_picture', 'doctors'
        ]

    def get_doctors(self, obj):
        """Retrieve the list of doctors treating this patient."""
        doctors = obj.assigned_doctors.all()

        if not doctors:  # Avoids unnecessary `.exists()` query
            return [{"id": None, "first_name": "No Doctor", "last_name": "Assigned", "specialization": "N/A"}]

        return [
            {
                "id": doctor.id,
                "first_name": doctor.user.first_name,
                "last_name": doctor.user.last_name,
                "specialization": doctor.specialization
            }
            for doctor in doctors
        ]


class DoctorAvailabilityCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorAvailability
        fields = ['day', 'start_time', 'end_time']

    def create(self, validated_data):
        doctor = self.context['request'].user.doctor_profile
        validated_data['doctor'] = doctor
        return super().create(validated_data)




class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    role = serializers.ChoiceField(choices=("patient", "doctor"), default="patient")
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'phone', 'address', 'gender', 'profile_picture', 'password', 'role']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    def validate_phone(self, value):
        if value is None:
            return None
        return value.strip() or None





class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")

        # Authenticate the user
        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("Invalid username or password.")

        # Debugging: Print user details
        print(f"User: {user.username}, ID: {user.id}")

        # Get the user's role (with a default value if role is not defined)
        role = getattr(user, "role", "unknown")
        print(f"User role: {role}")  # Debugging: Print the role

        # Check if a profile exists for this user
        profile_required = False
        if role == "doctor":
            if not DoctorProfile.objects.filter(user=user).exists():
                profile_required = True
                print("Doctor profile is required.")  # Debugging
        elif role == "patient":
            if not PatientProfile.objects.filter(user=user).exists():
                profile_required = True
                print("Patient profile is required.")  # Debugging

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                 "role": getattr(user, "role", "unknown"),
                "profile_required": profile_required,  
            },
        }

