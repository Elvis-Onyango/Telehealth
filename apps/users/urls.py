from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, LoginView, LogoutView, 
    RegisterPageView, LoginPageView, 
    DoctorListPageView, PatientDashboardPageView, 
    PatientProfileView, DoctorDashboardView, 
    DoctorPatientsListView, doctor_dashboard, 
    DoctorListView, PatientProfileCreationView,
    DisplayPatientFormView, DoctorProfileCreationView,
    DisplayDoctorFormView, WeekdayListCreateView,
    MessageListCreateView, ConversationListView, ConversationDetailView
)

app_name = 'users'

urlpatterns = [
    # --------------------------
    # Authentication API Endpoints
    # --------------------------
    path('signup/', RegisterView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # --------------------------
    # Authentication Pages
    # --------------------------
    path('login-page/', LoginPageView.as_view(), name='login-page'),
    path('register-page/', RegisterPageView.as_view(), name='register-page'),
    
    # --------------------------
    # Doctor Related Endpoints
    # --------------------------
    path('doctor-page/', DoctorListPageView.as_view(), name='doctor-page'),  
    path('doctor/profile/', DoctorDashboardView.as_view(), name='doctor-profile'),
    path('doctor/patients/', DoctorPatientsListView.as_view(), name='doctor-patients'),
    path('doctors-list/', DoctorListView.as_view(), name='doctors-list'), 
    path('dashboard/', doctor_dashboard, name='doctor-dashboard'),
    path('doctor/create/', DoctorProfileCreationView.as_view(), name='doctor-create-profile'),
    path('doctor-profile-create/', DisplayDoctorFormView.as_view(), name='doctor-profile-create'),  
    
    # --------------------------
    # Patient Related Endpoints
    # --------------------------
    path('patient/profile/', PatientProfileView.as_view(), name='patient-profile'),
    path('patient/create/', PatientProfileCreationView.as_view(), name='patient-create-profile'),
    path('patient-profile-create/', DisplayPatientFormView.as_view(), name='patient-profile-create'),
    path('patient-dashboard/', PatientDashboardPageView.as_view(), name='patient-dashboard'),
    
    # --------------------------
    # Weekday Endpoints
    # --------------------------
    path('week/', WeekdayListCreateView.as_view(), name='week'),
    
    # --------------------------
    # Messaging Endpoints
    # --------------------------
    path('messages/', MessageListCreateView.as_view(), name='message-list'),
    path('messages/conversations/', ConversationListView.as_view(), name='conversation-list'),
    path('messages/conversations/<int:user_id>/', ConversationDetailView.as_view(), name='conversation-detail'),
    

]