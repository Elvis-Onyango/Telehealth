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
from .models import User, DoctorProfile, PatientProfile,Weekday
from apps.appointments.models import Appointment
from .serializers import (
    RegisterSerializer, LoginSerializer,
    UserSerializer, DoctorProfileSerializer,
    PatientProfileSerializer,WeekdaySerializer,  DoctorAvailabilityCreateSerializer
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
    API for user login - Returns JWT token, sets session login, and user role.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if user:
            # Set Django session login so @login_required works
            login(request, user)

            # JWT generation
            refresh = RefreshToken.for_user(user)

            # Role logic
            role = getattr(user, "role", "user")

            profile_required = False
            if role == "doctor" and not DoctorProfile.objects.filter(user=user).exists():
                profile_required = True
            elif role == "patient" and not PatientProfile.objects.filter(user=user).exists():
                profile_required = True

            return Response({
                "message": "Login successful",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "role": role,
                "profile_required": profile_required,
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

class AddDoctorAvailabilityView(generics.CreateAPIView):
    serializer_class = DoctorAvailabilityCreateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DoctorAvailability.objects.filter(doctor=self.request.user.doctor_profile)



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



from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import DoctorProfile, Weekday
from .forms import DoctorProfileUpdateForm, UserUpdateForm
from apps.appointments.models import Hospital

@login_required
def doctor_profile_view(request):
    try:
        doctor_profile = request.user.doctor_profile
    except DoctorProfile.DoesNotExist:
        messages.info(request, 'Please complete your doctor profile first.')
    
    context = {
        'doctor_profile': doctor_profile,
        'available_days': doctor_profile.available_days.all(),
        'hospital_list': Hospital.objects.all(),
        'weekdays': Weekday.objects.all()
    }
    return render(request, 'users/profile_view.html', context)

@login_required
def doctor_profile_update(request):
    try:
        doctor_profile = request.user.doctor_profile
    except DoctorProfile.DoesNotExist:
        messages.info(request, 'Please complete your doctor profile first.')
        #return redirect('complete_doctor_profile')  # exit if profile not found

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        profile_form = DoctorProfileUpdateForm(request.POST, request.FILES, instance=doctor_profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile = profile_form.save(commit=False)
            profile.save()
            profile_form.save_m2m()
            messages.success(request, 'Your profile has been updated!')
            return redirect('users:doctor_profile_view')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = DoctorProfileUpdateForm(instance=doctor_profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'hospital_list': Hospital.objects.all(),
        'weekdays': Weekday.objects.all()
    }
    return render(request, 'users/profile_update.html', context)
