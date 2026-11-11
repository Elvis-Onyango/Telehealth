from datetime import time, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.appointments.models import Appointment, Billing, Hospital, HospitalAdministrator
from apps.notifications.models import Notification
from apps.pharmacy.models import Order
from apps.prescriptions.models import MedicalHistory, MedicalReport, Prescription
from .models import DoctorProfile, PatientProfile
from .forms import DoctorProfileUpdateForm


User = get_user_model()


class DemoDataCommandTests(TestCase):
    def test_seed_demo_data_is_repeatable_and_keeps_existing_accounts(self):
        existing_user = User.objects.create_user(
            username="existing-account",
            password="Existing-Password-839!",
            role="patient",
        )
        original_count = User.objects.count()

        call_command("seed_demo_data", password="Local-Demo-Password-482!")
        counts_after_first_run = {
            "users": User.objects.count(),
            "hospitals": Hospital.objects.count(),
            "appointments": Appointment.objects.count(),
            "billings": Billing.objects.count(),
        }
        call_command("seed_demo_data", password="Different-Password-281!")
        counts_after_second_run = {
            "users": User.objects.count(),
            "hospitals": Hospital.objects.count(),
            "appointments": Appointment.objects.count(),
            "billings": Billing.objects.count(),
        }

        self.assertEqual(User.objects.count() - original_count, 15)
        self.assertEqual(Hospital.objects.count(), 3)
        self.assertEqual(Appointment.objects.count(), 5)
        self.assertEqual(Billing.objects.count(), 5)
        self.assertEqual(counts_after_first_run, counts_after_second_run)
        self.assertTrue(existing_user.check_password("Existing-Password-839!"))
        self.assertTrue(
            User.objects.get(username="demo_superadmin").is_superuser
        )
        self.assertEqual(
            HospitalAdministrator.objects.filter(user__username__startswith="demo_").count(),
            3,
        )
        self.assertEqual(
            DoctorProfile.objects.filter(user__username__startswith="demo_").count(),
            5,
        )
        self.assertEqual(
            PatientProfile.objects.filter(user__username__startswith="demo_").count(),
            6,
        )


class RegistrationAndLoginTests(APITestCase):
    def setUp(self):
        self.signup_url = reverse("users:signup")
        self.login_url = reverse("users:login")
        self.registration_data = {
            "first_name": "Avery",
            "last_name": "Patient",
            "username": "avery-patient",
            "email": "avery@example.test",
            "password": "Safe-Password-729!",
            "role": "patient",
        }

    def test_patient_signup_login_and_session_flow(self):
        signup_response = self.client.post(
            self.signup_url,
            self.registration_data,
            format="json",
        )

        self.assertEqual(signup_response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="avery-patient")
        self.assertTrue(user.check_password(self.registration_data["password"]))
        self.assertTrue(hasattr(user, "patient_profile"))

        login_response = self.client.post(
            self.login_url,
            {
                "username": self.registration_data["username"],
                "password": self.registration_data["password"],
            },
            format="json",
        )

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertEqual(login_response.data["role"], "patient")
        self.assertFalse(login_response.data["profile_required"])
        self.assertTrue(login_response.data["access"])
        self.assertTrue(login_response.data["refresh"])

        dashboard_response = self.client.get(reverse("users:patient-dashboard"))
        self.assertEqual(dashboard_response.status_code, status.HTTP_200_OK)

    def test_doctor_signup_and_login_returns_doctor_dashboard_role(self):
        data = {
            **self.registration_data,
            "username": "avery-doctor",
            "email": "doctor@example.test",
            "role": "doctor",
        }
        signup_response = self.client.post(self.signup_url, data, format="json")
        self.assertEqual(signup_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.get(username="avery-doctor").doctor_profile)

        login_response = self.client.post(
            self.login_url,
            {"username": data["username"], "password": data["password"]},
            format="json",
        )

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertEqual(login_response.data["role"], "doctor")
        self.assertFalse(login_response.data["profile_required"])

    def test_public_signup_cannot_create_hospital_admin(self):
        data = {**self.registration_data, "role": "admin"}

        response = self.client.post(self.signup_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username=data["username"]).exists())

    def test_signup_rejects_weak_password(self):
        data = {**self.registration_data, "password": "password"}

        response = self.client.post(self.signup_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_signup_normalizes_empty_phone_to_null(self):
        first = {
            **self.registration_data,
            "username": "no-phone-one",
            "phone": "",
        }
        second = {
            **self.registration_data,
            "username": "no-phone-two",
            "phone": "",
        }

        first_response = self.client.post(self.signup_url, first, format="json")
        second_response = self.client.post(self.signup_url, second, format="json")

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(User.objects.get(username="no-phone-one").phone)
        self.assertIsNone(User.objects.get(username="no-phone-two").phone)

    def test_login_rejects_invalid_password(self):
        User.objects.create_user(
            username="existing-patient",
            password="Safe-Password-729!",
            role="patient",
        )

        response = self.client.post(
            self.login_url,
            {"username": "existing-patient", "password": "incorrect"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_defaults_role_and_normalizes_blank_phone(self):
        user = User.objects.create_user(
            username="default-role-user",
            password="Safe-Password-729!",
            phone="   ",
        )

        self.assertEqual(user.role, "patient")
        self.assertIsNone(user.phone)

    def test_superuser_login_is_identified_for_superadmin_redirect(self):
        User.objects.create_superuser(
            username="site-superuser",
            password="Safe-Password-729!",
        )

        response = self.client.post(
            self.login_url,
            {"username": "site-superuser", "password": "Safe-Password-729!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], "admin")
        self.assertTrue(response.data["is_superuser"])

    def test_login_honors_remember_me_session_expiry(self):
        User.objects.create_user(
            username="remember-user",
            password="Safe-Password-729!",
            role="patient",
        )

        response = self.client.post(
            self.login_url,
            {
                "username": "remember-user",
                "password": "Safe-Password-729!",
                "remember_me": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.client.session.get_expire_at_browser_close())

    def test_logout_ends_the_authenticated_session(self):
        user = User.objects.create_user(
            username="logout-user",
            password="Safe-Password-729!",
            role="patient",
        )
        self.client.force_login(user)

        response = self.client.post(reverse("users:logout"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("_auth_user_id", self.client.session)


class DashboardPageAccessTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(
            username="page-patient",
            password="Safe-Password-729!",
            role="patient",
        )
        self.doctor = User.objects.create_user(
            username="page-doctor",
            password="Safe-Password-729!",
            role="doctor",
        )
        self.hospital = Hospital.objects.create(
            name="Test Hospital",
            address="1 Main Street",
            contact="555-0131",
        )
        self.hospital_admin = User.objects.create_user(
            username="page-hospital-admin",
            password="Safe-Password-729!",
            role="admin",
            is_staff=False,
        )
        HospitalAdministrator.objects.create(
            user=self.hospital_admin,
            hospital=self.hospital,
        )

    def test_signup_and_login_pages_render_expected_fields(self):
        signup_response = self.client.get(reverse("users:register-page"))
        login_response = self.client.get(reverse("users:login-page"))

        self.assertEqual(signup_response.status_code, status.HTTP_200_OK)
        self.assertContains(signup_response, 'name="role" value="patient"')
        self.assertContains(signup_response, 'name="role" value="doctor"')
        self.assertNotContains(signup_response, 'name="role" value="admin"')
        self.assertNotContains(signup_response, 'value="other"')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertContains(login_response, 'id="login-form"')
        self.assertContains(login_response, "/api/users/login/")

    def test_doctor_directory_renders_search_filters_and_booking_flow(self):
        response = self.client.get(reverse("users:doctor-page"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'id="search-input"')
        self.assertContains(response, 'id="specialty-filter"')
        self.assertContains(response, 'id="hospital-filter"')
        self.assertContains(response, 'id="availability-filter"')
        self.assertContains(response, "/api/users/doctors-list/")
        self.assertContains(response, "/api/appointments/appointments/")
        self.assertContains(response, "Request appointment")
        self.assertNotContains(response, "120 reviews")
        self.assertNotContains(response, "4.8")

    def test_patient_dashboard_requires_login_and_patient_role(self):
        url = reverse("users:patient-dashboard")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('users:login-page')}?next={url}")

        self.client.force_login(self.doctor)
        self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.patient)
        self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)

    @patch("apps.appointments.signals.send_sms")
    def test_patient_dashboard_renders_their_backend_appointments_only(self, send_sms):
        doctor_profile = self.doctor.doctor_profile
        self.patient.patient_profile.assigned_doctors.add(doctor_profile)
        appointment = Appointment.objects.create(
            patient=self.patient.patient_profile,
            doctor=doctor_profile,
            hospital=self.hospital,
            date=timezone.localdate() + timedelta(days=4),
            time=time(9, 30),
            notes="Private clinical detail",
        )
        Billing.objects.create(
            appointment=appointment,
            total_fee=Decimal("125.00"),
            payment_method="mpesa",
        )

        self.client.force_login(self.patient)
        response = self.client.get(reverse("users:patient-dashboard"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Welcome, page-patient.")
        self.assertContains(response, "Upcoming appointments")
        self.assertContains(response, "KSh 0.00")
        self.assertNotContains(response, "Private clinical detail")

    def test_patient_dashboard_shows_private_notifications_records_and_orders(self):
        MedicalHistory.objects.create(
            patient=self.patient.patient_profile,
            allergies="Pollen allergy",
        )
        Prescription.objects.create(
            patient=self.patient.patient_profile,
            doctor=self.doctor.doctor_profile,
            encrypted_prescription="not-valid-encrypted-data",
        )
        MedicalReport.objects.create(
            patient=self.patient.patient_profile,
            doctor=self.doctor.doctor_profile,
            diagnosis="Private diagnosis",
        )
        Order.objects.create(user=self.patient, total_price=Decimal("90.00"))
        Notification.objects.create(user=self.patient, message="Appointment reminder")

        self.client.force_login(self.patient)
        response = self.client.get(reverse("users:patient-dashboard"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Appointment reminder")
        self.assertContains(response, "Pollen allergy")
        self.assertContains(response, "Recent prescriptions & reports")
        self.assertContains(response, "Private diagnosis")
        self.assertContains(response, "Pharmacy orders")
        self.assertContains(response, "KSh 90.00")

    def test_doctor_dashboard_requires_login_and_doctor_role(self):
        url = reverse("users:doctor-dashboard")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('users:login-page')}?next={url}")

        self.client.force_login(self.patient)
        self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.doctor)
        self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)

    @patch("apps.appointments.signals.send_sms")
    def test_doctor_dashboard_renders_appointments_and_connected_patients(self, send_sms):
        appointment = Appointment.objects.create(
            patient=self.patient.patient_profile,
            doctor=self.doctor.doctor_profile,
            hospital=self.hospital,
            date=timezone.localdate() + timedelta(days=4),
            time=time(10, 30),
            notes="Do not expose clinical notes",
        )
        self.client.force_login(self.doctor)

        response = self.client.get(reverse("users:doctor-dashboard"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Appointments")
        self.assertContains(response, "page-patient")
        self.assertContains(response, "1 upcoming")
        self.assertNotContains(response, "Do not expose clinical notes")

    def test_doctor_dashboard_shows_notifications_and_own_clinical_activity(self):
        Prescription.objects.create(
            patient=self.patient.patient_profile,
            doctor=self.doctor.doctor_profile,
            encrypted_prescription="prescription data",
        )
        MedicalReport.objects.create(
            patient=self.patient.patient_profile,
            doctor=self.doctor.doctor_profile,
            diagnosis="Diagnosis",
        )
        Notification.objects.create(user=self.doctor, message="Schedule updated")
        self.client.force_login(self.doctor)

        response = self.client.get(reverse("users:doctor-dashboard"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Schedule updated")
        self.assertContains(response, "Recent clinical activity")
        self.assertContains(response, "Prescription ·")
        self.assertContains(response, "Medical report ·")

    def test_doctor_cannot_change_hospital_assignment_from_profile_settings(self):
        self.assertNotIn("hospital", DoctorProfileUpdateForm().fields)

        self.client.force_login(self.patient)
        response = self.client.get(reverse("users:doctor_profile_update"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_hospital_admin_login_redirects_to_hospital_dashboard(self):
        response = self.client.post(
            reverse("custom-admin-login"),
            {
                "username": "page-hospital-admin",
                "password": "Safe-Password-729!",
            },
        )

        self.assertRedirects(response, reverse("hospital-dashboard"))

    def test_hospital_login_alias_redirects_hospital_admin_to_dashboard(self):
        response = self.client.post(
            reverse("hospital-login"),
            {
                "username": "page-hospital-admin",
                "password": "Safe-Password-729!",
            },
        )

        self.assertRedirects(response, reverse("hospital-dashboard"))

    def test_admin_login_allows_switching_from_an_existing_user_session(self):
        self.client.force_login(self.patient)

        login_page = self.client.get(reverse("custom-admin-login"))
        self.assertEqual(login_page.status_code, status.HTTP_200_OK)

        response = self.client.post(
            reverse("custom-admin-login"),
            {
                "username": "page-hospital-admin",
                "password": "Safe-Password-729!",
            },
        )

        self.assertRedirects(response, reverse("hospital-dashboard"))
        self.assertEqual(
            str(self.client.session["_auth_user_id"]),
            str(self.hospital_admin.pk),
        )

    def test_superadmin_login_redirects_to_superadmin_dashboard(self):
        User.objects.create_superuser(
            username="dashboard-superadmin",
            password="Safe-Password-729!",
        )

        response = self.client.post(
            reverse("custom-admin-login"),
            {
                "username": "dashboard-superadmin",
                "password": "Safe-Password-729!",
            },
        )

        self.assertRedirects(response, reverse("superadmin-dashboard"))

    def test_hospital_admin_cannot_open_superadmin_dashboard(self):
        self.client.force_login(self.hospital_admin)

        response = self.client.get(reverse("superadmin-dashboard"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
