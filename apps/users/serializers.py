from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User, DoctorProfile, PatientProfile, Weekday,Message
from apps.appointments.serializers import HospitalSerializer

from apps.prescriptions.serializers import MedicalHistorySerializer, MedicalReportSerializer


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'address', 'gender', 'role', 'profile_picture']

class WeekdaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Weekday
        fields = ['id','day']


class DoctorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # Fetch full user details
    available_days = WeekdaySerializer(many=True, read_only=True)  # Fetch full weekday names
    hospital = HospitalSerializer(read_only = True)

    class Meta:
        model = DoctorProfile
        fields = [
            'id', 'user', 'specialization', 'hospital', 'available_days',
            'consultation_fee', 'years_of_experience', 'license_number',
            'certifications', 'profile_picture'
        ]

    def create(self, validated_data):
        """Create a doctor profile"""
        available_days = validated_data.pop('available_days', [])
        doctor_profile = DoctorProfile.objects.create(**validated_data)
        doctor_profile.available_days.set(available_days)
        return doctor_profile


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



class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'phone', 'address', 'gender', 'profile_picture', 'password', 'role']

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data["password"])
        return User.objects.create(**validated_data)





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





class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    recipient = UserSerializer(read_only=True)
    
    sender_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='sender', 
        write_only=True
    )
    recipient_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='recipient', 
        write_only=True
    )
    
    file_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'recipient', 'content',
            'file', 'file_url', 'video', 'video_url',
            'link', 'timestamp', 'is_read', 'message_type',
            'sender_id', 'recipient_id'
        ]
        read_only_fields = ['timestamp', 'is_read', 'message_type']

    def get_file_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.file.url) if obj.file else None

    def get_video_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.video.url) if obj.video else None

    def validate(self, data):
        sender = data.get('sender')
        recipient = data.get('recipient')

        if sender and recipient:
            if not ((sender.role == 'doctor' and recipient.role == 'patient') or 
                    (sender.role == 'patient' and recipient.role == 'doctor')):
                raise serializers.ValidationError("Messages can only be sent between doctors and patients")

        if not any([data.get('content'), data.get('file'), data.get('video'), data.get('link')]):
            raise serializers.ValidationError("Message must contain either content, file, video, or link")

        return data
