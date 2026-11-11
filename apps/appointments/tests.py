from datetime import time, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.admin_auth.models import AuditEvent
from apps.messaging.models import Message
from apps.notifications.models import Notification
from apps.pharmacy.models import Order, OrderItem, PharmacyItem
from apps.prescriptions.models import MedicalHistory, MedicalReport

from .models import Appointment, Billing, Hospital, HospitalAdministrator


User = get_user_model()


class AppointmentBookingTests(APITestCase):
    def setUp(self):
        self.patient_user = User.objects.create_user(
            username="patient",
            password="test-password",
            role="patient",
            first_name="Pat",
            last_name="One",
        )
        self.patient = self.patient_user.patient_profile
        self.doctor_user = User.objects.create_user(
            username="doctor",
            password="test-password",
            role="doctor",
            first_name="Doc",
            last_name="One",
        )
        self.doctor = self.doctor_user.doctor_profile
        self.doctor.specialization = "Family Medicine"
        self.doctor.consultation_fee = Decimal("150.25")
        self.doctor.license_number = "DOC-001"
        self.doctor.save()
        self.booking_date = timezone.localdate() + timedelta(days=7)
        self.booking_time = time(10, 30)
        self.url = reverse("appointment-list")
        self.payload = {
            "doctor": self.doctor.pk,
            "date": self.booking_date.isoformat(),
            "time": self.booking_time.isoformat(),
            "type": "virtual",
            "notes": "Follow-up consultation",
            "payment_method": "mpesa",
            "total_fee": "0.01",
        }
        self.client.force_authenticate(user=self.patient_user)

    @patch("apps.appointments.signals.send_sms")
    def test_booking_uses_doctor_fee_and_creates_pending_billing(self, send_sms):
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["consultation_fee"], "150.25")
        self.assertEqual(response.data["payment_status"], "pending")
        self.assertTrue(response.data["video_call_link"])

        appointment = Appointment.objects.get(pk=response.data["id"])
        meeting_url = reverse(
            "videoconferencing:video_meeting",
            kwargs={"meeting_id": appointment.video_call.meeting_id},
        )
        self.assertEqual(
            response.data["video_call_link"],
            f"http://testserver{meeting_url}",
        )
        self.assertEqual(appointment.video_call.host, self.doctor_user)
        self.assertTrue(
            appointment.video_call.participants.filter(pk=self.patient_user.pk).exists()
        )
        self.assertEqual(appointment.patient, self.patient)
        self.assertEqual(appointment.doctor, self.doctor)
        self.assertTrue(self.doctor.patients.filter(pk=self.patient.pk).exists())
        self.client.force_authenticate(user=self.patient_user)
        contact_response = self.client.get(reverse("message-contacts"))
        self.assertEqual(contact_response.status_code, status.HTTP_200_OK)
        self.assertEqual(contact_response.data[0]["id"], self.doctor_user.pk)
        self.assertEqual(appointment.hospital, self.doctor.hospital)
        self.assertEqual(appointment.billing.total_fee, Decimal("150.25"))
        self.assertEqual(appointment.billing.payment_method, "mpesa")
        self.assertEqual(appointment.billing.payment_status, "pending")

    @patch("apps.appointments.signals.send_sms")
    def test_reschedule_marks_appointment_and_creates_follow_up_link(self, send_sms):
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            hospital=self.doctor.hospital,
            date=self.booking_date,
            time=self.booking_time,
        )

        rescheduled = appointment.reschedule(
            new_date=self.booking_date + timedelta(days=2),
            new_time=time(11, 0),
            reason="Patient unavailable",
        )

        self.assertTrue(rescheduled.was_rescheduled)
        self.assertEqual(rescheduled.status, "pending")
        self.assertEqual(rescheduled.reschedule_reason, "Patient unavailable")
        self.assertEqual(rescheduled.date, self.booking_date + timedelta(days=2))
        self.assertEqual(rescheduled.time, time(11, 0))

    @patch("apps.appointments.signals.send_sms")
    def test_no_show_and_follow_up_can_be_recorded(self, send_sms):
        original = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            hospital=self.doctor.hospital,
            date=self.booking_date,
            time=self.booking_time,
        )

        original.mark_no_show()
        self.assertEqual(original.status, "no_show")

        follow_up = original.create_follow_up(
            new_date=self.booking_date + timedelta(days=7),
            new_time=time(12, 0),
        )

        self.assertEqual(follow_up.follow_up_of, original)
        self.assertEqual(follow_up.status, "pending")
        self.assertIn(follow_up, list(original.follow_ups.all()))

    @patch("apps.appointments.signals.send_sms")
    def test_virtual_meeting_link_is_shown_to_both_appointment_users(self, send_sms):
        response = self.client.post(self.url, self.payload, format="json")
        appointment = Appointment.objects.get(pk=response.data["id"])
        meeting_url = reverse(
            "videoconferencing:video_meeting",
            kwargs={"meeting_id": appointment.video_call.meeting_id},
        )

        self.client.force_login(self.patient_user)
        patient_dashboard = self.client.get(reverse("users:patient-dashboard"))
        self.assertContains(patient_dashboard, f'href="{meeting_url}"')
        self.assertContains(
            patient_dashboard,
            f'?contact={self.doctor_user.pk}',
        )
        self.assertContains(patient_dashboard, "Message doctor")

        self.client.force_login(self.doctor_user)
        doctor_dashboard = self.client.get(reverse("users:doctor-dashboard"))
        self.assertContains(doctor_dashboard, f'href="{meeting_url}"')
        self.assertContains(doctor_dashboard, "Message patient")

        other_user = User.objects.create_user(
            username="unrelated-patient",
            password="Safe-Password-729!",
            role="patient",
        )
        self.client.force_login(other_user)
        unauthorized_response = self.client.get(meeting_url)
        self.assertEqual(
            unauthorized_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    @patch("apps.appointments.signals.send_sms")
    def test_physical_appointment_does_not_create_video_call(self, send_sms):
        response = self.client.post(
            self.url,
            {**self.payload, "type": "physical"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data["video_call_link"])
        appointment = Appointment.objects.get(pk=response.data["id"])
        self.assertFalse(hasattr(appointment, "video_call"))

    @patch("apps.appointments.signals.send_sms")
    def test_waiting_room_and_meeting_templates_resolve_video_routes(self, send_sms):
        response = self.client.post(self.url, self.payload, format="json")
        appointment = Appointment.objects.get(pk=response.data["id"])
        meeting_url = reverse(
            "videoconferencing:video_meeting",
            kwargs={"meeting_id": appointment.video_call.meeting_id},
        )
        waiting_url = reverse(
            "videoconferencing:waiting_room",
            kwargs={"meeting_id": appointment.video_call.meeting_id},
        )
        self.client.force_login(self.patient_user)

        waiting_response = self.client.get(waiting_url)
        self.assertEqual(waiting_response.status_code, status.HTTP_200_OK)
        self.assertContains(waiting_response, meeting_url)

        appointment.video_call.scheduled_time = timezone.now() - timedelta(minutes=5)
        appointment.video_call.save(update_fields=["scheduled_time"])
        meeting_response = self.client.get(meeting_url)
        self.assertEqual(meeting_response.status_code, status.HTTP_200_OK)
        self.assertContains(meeting_response, reverse("users:patient-dashboard"))

    @patch("apps.appointments.signals.send_sms")
    def test_occupied_time_cannot_be_booked_twice(self, send_sms):
        first_response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)

        second_response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("time", second_response.data)
        self.assertEqual(Appointment.objects.count(), 1)
        self.assertEqual(Billing.objects.count(), 1)

    @patch("apps.appointments.signals.send_sms")
    def test_booking_rejects_doctor_unavailable_on_selected_day(self, send_sms):
        from apps.users.models import Weekday

        unavailable_day = (
            self.booking_date + timedelta(days=1)
        ).strftime("%A").lower()
        self.doctor.available_days.add(Weekday.objects.create(day=unavailable_day))

        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("date", response.data)
        self.assertFalse(Appointment.objects.exists())

    def test_non_patients_cannot_book_appointments(self):
        self.client.force_authenticate(user=self.doctor_user)

        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Appointment.objects.exists())

    @patch("apps.appointments.signals.send_sms")
    def test_patient_list_only_includes_their_appointments(self, send_sms):
        created = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        patient_response = self.client.get(self.url)
        self.assertEqual(patient_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(patient_response.data), 1)
        self.assertEqual(patient_response.data[0]["id"], created.data["id"])
        self.assertEqual(patient_response.data[0]["doctor_name"], "Doc One")

        other_user = User.objects.create_user(
            username="other-patient",
            password="test-password",
            role="patient",
        )
        self.client.force_authenticate(user=other_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_invalid_payment_method_is_rejected(self):
        self.payload["payment_method"] = "cash"

        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("payment_method", response.data)
        self.assertFalse(Appointment.objects.exists())


class HospitalDashboardAccessTests(APITestCase):
    def setUp(self):
        self.hospital = Hospital.objects.create(
            name="North Clinic",
            address="1 Main Street",
            contact="555-0101",
            email="north@example.test",
        )
        self.other_hospital = Hospital.objects.create(
            name="South Clinic",
            address="2 Main Street",
            contact="555-0102",
            email="south@example.test",
        )
        self.admin = User.objects.create_user(
            username="north-admin",
            password="test-password-123",
            role="admin",
            first_name="North",
            last_name="Admin",
        )
        HospitalAdministrator.objects.create(user=self.admin, hospital=self.hospital)
        self.patient_user = User.objects.create_user(
            username="dashboard-patient",
            password="test-password-123",
            role="patient",
            first_name="Pat",
            last_name="One",
            phone="555-0103",
        )
        self.doctor_user = User.objects.create_user(
            username="north-doctor",
            password="test-password-123",
            role="doctor",
            first_name="Doc",
            last_name="North",
        )
        self.doctor = self.doctor_user.doctor_profile
        self.doctor.hospital = self.hospital
        self.doctor.save(update_fields=["hospital"])
        self.other_doctor_user = User.objects.create_user(
            username="south-doctor",
            password="test-password-123",
            role="doctor",
            first_name="Doc",
            last_name="South",
        )
        self.other_doctor = self.other_doctor_user.doctor_profile
        self.other_doctor.hospital = self.other_hospital
        self.other_doctor.save(update_fields=["hospital"])
        self.other_patient_user = User.objects.create_user(
            username="south-patient",
            password="test-password-123",
            role="patient",
            first_name="Pat",
            last_name="South",
        )
        self.appointment = Appointment.objects.create(
            patient=self.patient_user.patient_profile,
            doctor=self.doctor,
            hospital=self.hospital,
            date=timezone.localdate() + timedelta(days=5),
            time=time(10, 0),
            notes="Private clinical note",
        )
        self.billing = Billing.objects.create(
            appointment=self.appointment,
            total_fee=Decimal("125.00"),
            payment_method="mpesa",
        )
        self.other_appointment = Appointment.objects.create(
            patient=self.other_patient_user.patient_profile,
            doctor=self.other_doctor,
            hospital=self.other_hospital,
            date=timezone.localdate() + timedelta(days=5),
            time=time(11, 0),
        )
        self.client.force_login(self.admin)
        self.client.raise_request_exception = False

    def test_hospital_admin_dashboard_is_limited_to_assigned_hospital(self):
        Notification.objects.create(user=self.admin, message="Billing review required")
        response = self.client.get(reverse("hospital-dashboard"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, self.hospital.name)
        self.assertContains(response, "Doc North")
        self.assertNotContains(response, self.other_hospital.name)
        self.assertNotContains(response, "Doc South")
        self.assertNotContains(response, "Private clinical note")
        self.assertContains(response, "Billing review required")
        self.assertContains(response, "Pending payments")
        self.assertContains(response, "Paid total")
        self.assertContains(response, 'data-dashboard-target="hospital-appointments-panel"')
        self.assertNotContains(response, 'data-dashboard-target="accounts"')

    def test_hospital_admin_sees_patients_staff_and_reports_for_their_hospital(self):
        MedicalReport.objects.create(
            patient=self.patient_user.patient_profile,
            doctor=self.doctor,
            diagnosis="North lab finding",
        )
        response = self.client.get(reverse("hospital-dashboard"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Patients at North Clinic")
        self.assertContains(response, "Pat One")
        self.assertContains(response, "Doc North")
        self.assertContains(response, "North lab finding")
        self.assertNotContains(response, "Pat South")
        self.assertNotContains(response, "Doc South")
        self.assertNotContains(response, self.other_hospital.name)

    def test_hospital_admin_can_manage_global_pharmacy_inventory_and_orders(self):
        create_response = self.client.post(
            reverse("hospital-dashboard-action", args=["create_pharmacy_item"]),
            {
                "name": "Test medicine",
                "description": "Catalog entry",
                "price": "25.50",
                "stock": "12",
            },
        )
        item = PharmacyItem.objects.get(name="Test medicine")
        self.assertRedirects(create_response, reverse("hospital-dashboard"))
        self.assertEqual(item.stock, 12)

        order = Order.objects.create(user=self.other_patient_user, total_price="51.00")
        OrderItem.objects.create(order=order, pharmacy_item=item, quantity=2)
        response = self.client.post(
            reverse("hospital-dashboard-action", args=["update_pharmacy_order"]),
            {"object_id": order.pk, "status": "shipped"},
        )

        self.assertRedirects(response, reverse("hospital-dashboard"))
        order.refresh_from_db()
        self.assertEqual(order.status, "shipped")

        dashboard_response = self.client.get(reverse("hospital-dashboard"))
        self.assertContains(dashboard_response, "Test medicine")
        self.assertContains(dashboard_response, "Pat South")

        delete_response = self.client.post(
            reverse("hospital-dashboard-action", args=["delete_pharmacy_item"]),
            {"object_id": item.pk},
        )
        self.assertRedirects(delete_response, reverse("hospital-dashboard"))
        self.assertTrue(PharmacyItem.objects.filter(pk=item.pk).exists())
        self.assertContains(self.client.get(reverse("hospital-dashboard")), "cannot be deleted")

    def test_superadmin_dashboard_renders_live_hospital_directory(self):
        MedicalHistory.objects.create(
            patient=self.patient_user.patient_profile,
            allergies="Penicillin",
        )
        Message.objects.create(
            sender=self.patient_user,
            recipient=self.doctor_user,
            content="Private follow up",
        )
        superadmin = User.objects.create_superuser(
            username="directory-superadmin",
            password="test-password-123",
        )
        self.client.force_login(superadmin)

        response = self.client.get(reverse("superadmin-dashboard"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'data-dashboard-target="accounts"')
        self.assertContains(response, 'data-dashboard-target="hospitals"')
        self.assertContains(response, 'data-dashboard-target="messages"')
        self.assertContains(response, 'data-dashboard-target="orders"')
        self.assertContains(response, 'data-dashboard-target="video-calls"')
        self.assertContains(response, 'data-dashboard-target="audit-log"')
        self.assertContains(response, "Manage your care network")
        self.assertContains(response, self.hospital.name)
        self.assertContains(response, self.other_hospital.name)
        self.assertContains(response, "Create hospital administrator")
        self.assertContains(response, "System-wide overview")
        self.assertContains(response, "Recent clinical records")
        self.assertContains(response, "Recent private messages")
        self.assertContains(response, "Medical histories")
        self.assertContains(response, "Penicillin")
        self.assertContains(response, "Private follow up")
        self.assertEqual(
            response.context["global_model_rows"][0]["count"],
            User.objects.count(),
        )
        self.assertEqual(response.context["global_total_users"], User.objects.count())
        self.assertEqual(
            response.context["global_total_appointments"],
            Appointment.objects.count(),
        )
        self.assertEqual(len(response.context["global_appointment_months"]), 6)
        self.assertEqual(len(response.context["global_appointment_status_rows"]), 5)
        self.assertContains(response, "Appointment activity")
        self.assertContains(response, "Appointment status")
        self.assertTrue(
            any(
                row["label"] == "Appointments"
                and row["count"] == Appointment.objects.count()
                for row in response.context["global_model_rows"]
            )
        )
        self.assertEqual(
            AuditEvent.objects.filter(
                actor=superadmin,
                action="viewed_dashboard",
            ).count(),
            1,
        )

    def test_superadmin_can_send_individual_and_broadcast_notifications(self):
        superadmin = User.objects.create_superuser(
            username="notification-superadmin",
            password="Safe-Password-729!",
        )
        self.client.force_login(superadmin)
        url = reverse("hospital-dashboard-action", args=["send_notification"])

        individual_response = self.client.post(
            url,
            {
                "recipient": self.patient_user.pk,
                "message": "Your records are ready.",
            },
        )

        self.assertRedirects(individual_response, reverse("superadmin-dashboard"))
        self.assertTrue(
            Notification.objects.filter(
                user=self.patient_user,
                message="Your records are ready.",
            ).exists()
        )
        self.assertEqual(
            AuditEvent.objects.filter(action="sent_notification").latest(
                "created_at"
            ).details["recipient_count"],
            1,
        )

        expected_recipients = User.objects.count()
        broadcast_response = self.client.post(
            url,
            {"broadcast": "on", "message": "System maintenance notice."},
        )

        self.assertRedirects(broadcast_response, reverse("superadmin-dashboard"))
        self.assertEqual(
            Notification.objects.filter(
                message="System maintenance notice."
            ).count(),
            expected_recipients,
        )
        self.assertTrue(
            AuditEvent.objects.filter(
                action="sent_notification",
                details__broadcast=True,
                details__recipient_count=expected_recipients,
            ).exists()
        )

    def test_hospital_admin_cannot_send_system_notifications(self):
        response = self.client.post(
            reverse("hospital-dashboard-action", args=["send_notification"]),
            {"recipient": self.patient_user.pk, "message": "Unauthorized"},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Notification.objects.filter(message="Unauthorized").exists())

    @patch("apps.appointments.signals.send_sms")
    def test_hospital_admin_can_schedule_an_appointment(self, send_sms):
        appointment_date = timezone.localdate() + timedelta(days=6)
        response = self.client.post(
            reverse("hospital-dashboard-action", args=["create_appointment"]),
            {
                "hospital_id": self.hospital.pk,
                "patient": self.patient_user.patient_profile.pk,
                "doctor": self.doctor.pk,
                "date": appointment_date.isoformat(),
                "time": "11:00",
                "type": "physical",
                "status": "confirmed",
                "payment_method": "mpesa",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        created = Appointment.objects.get(date=appointment_date, time=time(11, 0))
        self.assertEqual(created.hospital, self.hospital)
        self.assertEqual(created.status, "confirmed")
        self.assertEqual(created.billing.payment_status, "pending")
        self.assertEqual(created.billing.total_fee, self.doctor.consultation_fee)

    def test_hospital_admin_patient_choices_are_hospital_scoped(self):
        from .forms import HospitalAppointmentForm

        form = HospitalAppointmentForm(hospital=self.hospital)

        self.assertIn(
            self.patient_user.patient_profile,
            form.fields["patient"].queryset,
        )
        self.assertNotIn(
            self.other_patient_user.patient_profile,
            HospitalAppointmentForm(hospital=self.hospital)
            .fields["patient"]
            .queryset,
        )

    def test_hospital_admin_cannot_mutate_another_hospital(self):
        response = self.client.post(
            reverse("hospital-dashboard-action", args=["update_hospital"]),
            {
                "hospital_id": self.other_hospital.pk,
                "name": "Changed",
                "address": "Changed",
                "contact": "555-0199",
                "email": "changed@example.test",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.other_hospital.refresh_from_db()
        self.assertEqual(self.other_hospital.name, "South Clinic")

    def test_hospital_api_write_is_limited_to_assigned_hospital(self):
        response = self.client.put(
            reverse("hospital-detail", args=[self.other_hospital.pk]),
            {"name": "Changed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_hospital_api_reads_are_limited_for_hospital_admins(self):
        list_response = self.client.get(reverse("hospital-list"))
        detail_response = self.client.get(
            reverse("hospital-detail", args=[self.other_hospital.pk])
        )

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [hospital["id"] for hospital in list_response.data],
            [self.hospital.pk],
        )
        self.assertEqual(detail_response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("apps.appointments.signals.send_sms")
    def test_cancel_keeps_billing_and_releases_active_slot(self, send_sms):
        response = self.client.post(
            reverse("hospital-dashboard-action", args=["cancel_appointment"]),
            {
                "hospital_id": self.hospital.pk,
                "object_id": self.appointment.pk,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, "cancelled")
        self.assertFalse(self.appointment.is_active)
        self.assertTrue(Billing.objects.filter(pk=self.billing.pk).exists())
        replacement = Appointment.objects.create(
            patient=self.patient_user.patient_profile,
            doctor=self.doctor,
            hospital=self.hospital,
            date=self.appointment.date,
            time=self.appointment.time,
        )
        self.assertTrue(replacement.is_active)

    def test_hospital_with_linked_data_cannot_be_deleted(self):
        superadmin = User.objects.create_superuser(
            username="superadmin",
            password="test-password-123",
        )
        self.client.force_login(superadmin)

        response = self.client.delete(reverse("hospital-detail", args=[self.hospital.pk]))

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(Hospital.objects.filter(pk=self.hospital.pk).exists())

    def test_unassigned_admin_cannot_open_dashboard(self):
        unassigned_admin = User.objects.create_user(
            username="unassigned-admin",
            password="test-password-123",
            role="admin",
        )
        self.client.force_login(unassigned_admin)

        response = self.client.get(reverse("hospital-dashboard"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superadmin_can_provision_a_non_staff_hospital_admin(self):
        superadmin = User.objects.create_superuser(
            username="provisioning-superadmin",
            password="test-password-123",
        )
        self.client.force_login(superadmin)

        response = self.client.post(
            reverse("hospital-dashboard-action", args=["create_hospital_admin"]),
            {
                "username": "new-hospital-admin",
                "first_name": "Hospital",
                "last_name": "Admin",
                "email": "hospital-admin@example.test",
                "password": "Complex-Enough-Pass-723!",
                "hospital": self.hospital.pk,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        created = User.objects.get(username="new-hospital-admin")
        self.assertEqual(created.role, "admin")
        self.assertFalse(created.is_staff)
        self.assertEqual(created.hospital_administration.hospital, self.hospital)
