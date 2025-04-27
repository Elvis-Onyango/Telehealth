from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import RetrieveAPIView, GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from rest_framework_simplejwt.tokens import RefreshToken

import openai
import json
 

from apps.videoconferencing.models import VideoCall
from .models import User, DoctorProfile, PatientProfile,Weekday, Message
from apps.appointments.models import Appointment
from .serializers import (
    RegisterSerializer, LoginSerializer,
    UserSerializer, DoctorProfileSerializer,
    PatientProfileSerializer,WeekdaySerializer,MessageSerializer
)
from .permissions import IsAdmin, IsDoctor, IsPatient
from rest_framework import viewsets, status
from rest_framework.decorators import action





# ================================
#  USER AUTHENTICATION VIEWS
# ================================

class RegisterView(generics.CreateAPIView):
    """
    API for user registration (Signup)
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]  # Open for new users


class LoginView(APIView):
    """
    API for user login - Returns JWT token and user role.
    """
    permission_classes = [AllowAny]  # Anyone can access

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)

            # Get role directly from the user model
            role = getattr(user, "role", "user")  # Defaults to "user" if role is missing

            # Check if profile is required for doctors and patients
            profile_required = False
            if role == "doctor" and not DoctorProfile.objects.filter(user=user).exists():
                profile_required = True
            elif role == "patient" and not PatientProfile.objects.filter(user=user).exists():
                profile_required = True

            return Response({
                "message": "Login successful",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "role": role,  # Correctly assigned role
                "profile_required": profile_required,  # Helps frontend redirect
            })

        return Response({"message": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)



class LogoutView(APIView):
    """
    API to log out the user
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)


# ================================
#  PAGE RENDERING VIEWS (HTML)
# ================================

class LoginPageView(View):
    """ Renders the login page """
    def get(self, request):
        return render(request, 'users/login.html')

class RegisterPageView(View):
    """ Renders the signup page """
    def get(self, request):
        return render(request, 'users/register.html')

class PatientDashboardPageView(View):
    """ Renders the patient dashboard """
    def get(self, request):
        return render(request, 'users/patient_dashboard.html')

class DoctorListPageView(View):
    """ Renders the doctor list page """
    def get(self, request):
        return render(request, 'users/doctor_list.html')

def doctor_dashboard(request):
    return render(request, 'users/doctor_dashboard.html')

class DisplayPatientFormView(View):
    def get(self,request):
        return render(request,'users/patient_profilecreation_form.html')  


class DisplayDoctorFormView(View):
    def get(self,request):
        return render(request,'users/doctor_profileregistration_form.html')



# ================================
# DOCTOR & PATIENT MANAGEMENT APIS
# ================================

class DoctorDashboardView(generics.RetrieveAPIView):
    """
    API to fetch the currently logged-in doctor's profile.
    """
    serializer_class = DoctorProfileSerializer
    permission_classes = [IsDoctor]  # Only doctors can access

    def get_object(self):
        return DoctorProfile.objects.get(user=self.request.user)


class PatientPagination(PageNumberPagination):
    """
    Custom pagination for patients list
    """
    page_size = 10  
    page_size_query_param = 'page_size'
    max_page_size = 20


class DoctorPatientsListView(generics.ListAPIView):
    """
    API to list patients assigned to the logged-in doctor
    """
    serializer_class = PatientProfileSerializer  
    permission_classes = [IsDoctor]  
    pagination_class = PatientPagination  

    def get_queryset(self):
        """Retrieve all patients assigned to the logged-in doctor"""
        doctor = self.request.user.doctor_profile  
        return PatientProfile.objects.filter(assigned_doctors=doctor)  


class PatientDoctorsView(APIView):
    """
    API for a patient to fetch their assigned doctors.
    """
    permission_classes = [IsAuthenticated]  # Only authenticated patients

    def get(self, request, *args, **kwargs):
        patient = request.user.patient_profile  
        doctors = patient.doctors.all()  
        serializer = DoctorProfileSerializer(doctors, many=True)
        return Response(serializer.data)


class PatientProfileView(RetrieveAPIView):
    """
    API to fetch the currently logged-in patient's profile.
    """
    permission_classes = [IsAuthenticated]  
    serializer_class = PatientProfileSerializer  

    def get_object(self):
        return self.request.user.patient_profile

#create patient profile

class PatientProfileCreationView(generics.CreateAPIView):
    """Create a new Patient Profile"""
    serializer_class = PatientProfileSerializer
    permission_classes = [IsAuthenticated]  # Only logged-in users can create a profile

    def perform_create(self, serializer):
        """Saves profile with the logged-in user"""
        serializer.save(user=self.request.user)

# create doctor profile



class DoctorProfileCreationView(generics.CreateAPIView):
    queryset = DoctorProfile.objects.all()
    serializer_class = DoctorProfileSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Set the user before saving the serializer
        serializer.save(user=self.request.user)




class DoctorListView(generics.ListAPIView):
    """
    API to fetch the list of all doctors.
    """
    queryset = DoctorProfile.objects.all()
    serializer_class = DoctorProfileSerializer
    permission_classes = [AllowAny]  # Public API





#fetching week

class WeekdayListCreateView(generics.ListCreateAPIView):
    queryset = Weekday.objects.all()
    serializer_class = WeekdaySerializer
    permission_classes = [AllowAny]  


#===============================================
#Doctor patient Messaging
#================================================
from rest_framework.generics import ListCreateAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import Message, User
from .serializers import MessageSerializer, UserSerializer


class MessageListCreateView(ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(
            Q(sender=user) | Q(recipient=user)
        ).order_by('-timestamp').select_related('sender', 'recipient')

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


class ConversationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        partners = User.objects.filter(
            Q(sent_messages__recipient=user) | 
            Q(received_messages__sender=user)
        ).distinct()
        return Response(UserSerializer(partners, many=True).data)


class ConversationDetailView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer

    def get_queryset(self):
        user = self.request.user
        other_user_id = self.kwargs['user_id']
        return Message.objects.filter(
            Q(sender=user, recipient_id=other_user_id) |
            Q(sender_id=other_user_id, recipient=user)
        ).order_by('timestamp')

    def list(self, request, *args, **kwargs):
        # Mark all unread messages as read
        Message.objects.filter(
            recipient=request.user,
            sender_id=kwargs['user_id'],
            is_read=False
        ).update(is_read=True)
        return super().list(request, *args, **kwargs)






