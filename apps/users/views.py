from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

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
from apps.notifications.models import Notification
from apps.pharmacy.models import Order
from apps.prescriptions.models import MedicalHistory, MedicalReport, Prescription
from .models import User, DoctorProfile, PatientProfile,Weekday
from apps.appointments.models import Appointment, Billing
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
            remember_me = request.data.get("remember_me", False)
            request.session.set_expiry(1209600 if remember_me else 0)

            # JWT generation
            refresh = RefreshToken.for_user(user)

            # Role logic
            role = user.role or ("admin" if user.is_superuser else "user")

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
                "is_superuser": user.is_superuser,
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


@login_required(login_url="/api/users/login-page/")
@require_POST
def logout_page(request):
    logout(request)
    return redirect("users:login-page")


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

@method_decorator(login_required(login_url="/api/users/login-page/"), name="dispatch")
class PatientDashboardPageView(View):
    """ Renders the patient dashboard """
    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "patient":
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        try:
            patient = request.user.patient_profile
        except PatientProfile.DoesNotExist:
            return redirect("users:patient-profile-create")

        appointments = (
            Appointment.objects.filter(patient=patient)
            .select_related("doctor__user", "hospital", "billing", "video_call")
            .order_by("date", "time")
        )
        upcoming_appointments = appointments.filter(
            is_active=True,
            date__gte=timezone.localdate(),
        ).exclude(status="cancelled")
        doctors = DoctorProfile.objects.filter(
            Q(patients=patient)
            | Q(primary_patients=patient)
            | Q(appointments__patient=patient)
        ).select_related("user", "hospital").distinct()
        notifications = Notification.objects.filter(user=request.user).order_by(
            "-created_at",
            "-pk",
        )[:6]

        return render(
            request,
            "users/patient_dashboard.html",
            {
                "patient": patient,
                "appointments": appointments,
                "upcoming_appointments": upcoming_appointments,
                "doctors": doctors,
                "notifications": notifications,
                "unread_notifications_count": Notification.objects.filter(
                    user=request.user,
                    is_read=False,
                ).count(),
                "medical_history": MedicalHistory.objects.filter(patient=patient).first(),
                "prescriptions": Prescription.objects.filter(patient=patient)
                .select_related("doctor__user")
                .order_by("-date_issued")[:5],
                "medical_reports": MedicalReport.objects.filter(patient=patient)
                .select_related("doctor__user")
                .order_by("-date_issued")[:5],
                "pharmacy_orders": Order.objects.filter(user=request.user)
                .prefetch_related("items")
                .select_related("payment")
                .order_by("-ordered_at")[:5],
                "appointments_count": appointments.filter(is_active=True).count(),
                "upcoming_count": upcoming_appointments.count(),
                "paid_total": Billing.objects.filter(
                    appointment__patient=patient,
                    payment_status="paid",
                ).aggregate(total=Sum("total_fee"))["total"] or 0,
            },
        )

class DoctorListPageView(View):
    """ Renders the doctor list page """
    def get(self, request):
        return render(request, 'users/doctor_list.html')

@login_required(login_url="/api/users/login-page/")
def doctor_dashboard(request):
    if request.user.role != "doctor":
        raise PermissionDenied
    try:
        doctor = request.user.doctor_profile
    except DoctorProfile.DoesNotExist:
        return redirect("users:doctor-profile-create")

    appointments = (
        Appointment.objects.filter(doctor=doctor, is_active=True)
        .select_related("patient__user", "hospital", "video_call", "billing")
        .order_by("date", "time")
    )
    upcoming_appointments = appointments.filter(
        date__gte=timezone.localdate(),
        status__in=["pending", "confirmed"],
    )
    patients = PatientProfile.objects.filter(
        Q(assigned_doctors=doctor)
        | Q(primary_doctor=doctor)
        | Q(appointments__doctor=doctor)
    ).select_related("user").distinct()
    notifications = Notification.objects.filter(user=request.user).order_by(
        "-created_at",
        "-pk",
    )[:6]
    return render(
        request,
        "users/doctor_dashboard.html",
        {
            "doctor": doctor,
            "appointments": upcoming_appointments[:12],
            "appointments_count": appointments.count(),
            "upcoming_count": upcoming_appointments.count(),
            "today_count": upcoming_appointments.filter(
                date=timezone.localdate()
            ).count(),
            "patients": patients,
            "patients_count": patients.count(),
            "notifications": notifications,
            "unread_notifications_count": Notification.objects.filter(
                user=request.user,
                is_read=False,
            ).count(),
            "recent_prescriptions": Prescription.objects.filter(doctor=doctor)
            .select_related("patient__user")
            .order_by("-date_issued")[:5],
            "recent_medical_reports": MedicalReport.objects.filter(doctor=doctor)
            .select_related("patient__user")
            .order_by("-date_issued")[:5],
        },
    )

@method_decorator(login_required(login_url="/api/users/login-page/"), name="dispatch")
class DisplayPatientFormView(View):
    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "patient":
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get(self,request):
        return render(request,'users/patient_profilecreation_form.html')  


@method_decorator(login_required(login_url="/api/users/login-page/"), name="dispatch")
class DisplayDoctorFormView(View):
    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "doctor":
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

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
    permission_classes = [IsPatient]

    def get(self, request, *args, **kwargs):
        patient = request.user.patient_profile  
        doctors = patient.doctors.all()  
        serializer = DoctorProfileSerializer(doctors, many=True)
        return Response(serializer.data)


class PatientProfileView(RetrieveAPIView):
    """
    API to fetch the currently logged-in patient's profile.
    """
    permission_classes = [IsPatient]
    serializer_class = PatientProfileSerializer  

    def get_object(self):
        return self.request.user.patient_profile

#create patient profile

class PatientProfileCreationView(generics.CreateAPIView):
    """Create a new Patient Profile"""
    serializer_class = PatientProfileSerializer
    permission_classes = [IsPatient]

    def perform_create(self, serializer):
        """Saves profile with the logged-in user"""
        serializer.save(user=self.request.user)

# create doctor profile



class DoctorProfileCreationView(generics.CreateAPIView):
    queryset = DoctorProfile.objects.all()
    serializer_class = DoctorProfileSerializer
    permission_classes = [IsDoctor]

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
    if request.user.role != "doctor":
        raise PermissionDenied
    try:
        doctor_profile = request.user.doctor_profile
    except DoctorProfile.DoesNotExist:
        messages.info(request, 'Please complete your doctor profile first.')
        return redirect("users:doctor-profile-create")
    
    context = {
        'doctor_profile': doctor_profile,
        'available_days': doctor_profile.available_days.all(),
        'hospital_list': Hospital.objects.all(),
        'weekdays': Weekday.objects.all()
    }
    return render(request, 'users/profile_view.html', context)

@login_required
def doctor_profile_update(request):
    if request.user.role != "doctor":
        raise PermissionDenied
    try:
        doctor_profile = request.user.doctor_profile
    except DoctorProfile.DoesNotExist:
        messages.info(request, 'Please complete your doctor profile first.')
        return redirect("users:doctor-profile-create")

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
