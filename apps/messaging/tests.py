from django.core.files.uploadedfile import SimpleUploadedFile
from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.messaging.models import Message
from apps.appointments.models import Appointment
from django.utils import timezone
from datetime import time, timedelta
from telemedicine_project.asgi import application


User = get_user_model()


class MessagingApiTests(APITestCase):
    def setUp(self):
        self.doctor = User.objects.create_user(
            username="chat-doctor",
            password="test-password",
            role="doctor",
            first_name="Doctor",
            last_name="One",
        )
        self.patient = User.objects.create_user(
            username="chat-patient",
            password="test-password",
            role="patient",
            first_name="Patient",
            last_name="One",
        )
        self.other_patient = User.objects.create_user(
            username="other-patient",
            password="test-password",
            role="patient",
        )
        self.patient_profile = self.patient.patient_profile
        self.doctor.doctor_profile.patients.add(self.patient_profile)

    def test_contacts_are_limited_to_assigned_care_relationships(self):
        self.client.force_authenticate(user=self.patient)
        response = self.client.get(reverse("message-contacts"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [
            {"id": self.doctor.pk, "name": "Doctor One", "role": "doctor"}
        ])

        self.client.force_authenticate(user=self.doctor)
        response = self.client.get(reverse("message-contacts"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [
            {"id": self.patient.pk, "name": "Patient One", "role": "patient"}
        ])

    def test_booking_alone_creates_a_messaging_relationship(self):
        appointment = Appointment.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor.doctor_profile,
            date=timezone.localdate() + timedelta(days=4),
            time=time(10),
        )
        self.doctor.doctor_profile.patients.remove(self.patient_profile)

        self.client.force_authenticate(user=self.patient)
        contacts_response = self.client.get(reverse("message-contacts"))
        thread_response = self.client.get(
            reverse("message-thread", args=[self.doctor.pk])
        )
        send_response = self.client.post(
            reverse("send-message"),
            {
                "recipient": self.doctor.pk,
                "message_type": "text",
                "content": "I booked an appointment.",
            },
            format="json",
        )

        self.assertEqual(contacts_response.status_code, status.HTTP_200_OK)
        self.assertEqual(contacts_response.data[0]["id"], self.doctor.pk)
        self.assertEqual(thread_response.status_code, status.HTTP_200_OK)
        self.assertEqual(send_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Appointment.objects.filter(pk=appointment.pk).exists())

    def test_patient_can_send_and_list_messages_with_assigned_doctor(self):
        self.client.force_authenticate(user=self.patient)
        send_response = self.client.post(
            reverse("send-message"),
            {
                "recipient": self.doctor.pk,
                "message_type": "text",
                "content": "Hello, doctor.",
            },
            format="json",
        )

        self.assertEqual(send_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 1)

        list_response = self.client.get(
            reverse("message-thread", args=[self.doctor.pk])
        )
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data[0]["content"], "Hello, doctor.")
        self.assertEqual(list_response.data[0]["sender"]["id"], self.patient.pk)

    def test_chat_participants_can_share_files_through_protected_downloads(self):
        uploaded_file = SimpleUploadedFile(
            "prescription.pdf",
            b"demo prescription file",
            content_type="application/pdf",
        )
        self.client.force_authenticate(user=self.patient)
        send_response = self.client.post(
            reverse("send-message"),
            {
                "recipient": self.doctor.pk,
                "message_type": "file",
                "content": "Prescription attachment",
                "file": uploaded_file,
            },
            format="multipart",
        )

        self.assertEqual(send_response.status_code, status.HTTP_201_CREATED)
        self.assertIn("/api/messaging/messages/", send_response.data["file"])
        message = Message.objects.get()
        self.assertTrue(message.file)

        self.client.force_authenticate(user=self.doctor)
        download_response = self.client.get(
            reverse("message-attachment", args=[message.pk])
        )
        self.assertEqual(download_response.status_code, status.HTTP_200_OK)
        self.assertEqual(b"".join(download_response.streaming_content), b"demo prescription file")

        self.client.force_authenticate(user=self.other_patient)
        denied_response = self.client.get(
            reverse("message-attachment", args=[message.pk])
        )
        self.assertEqual(denied_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_jwt_file_upload_does_not_fall_back_to_session_csrf(self):
        uploaded_file = SimpleUploadedFile(
            "prescription.pdf",
            b"demo prescription file",
            content_type="application/pdf",
        )
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.patient)
        access_token = str(RefreshToken.for_user(self.patient).access_token)

        response = client.post(
            reverse("send-message"),
            {
                "recipient": self.doctor.pk,
                "message_type": "file",
                "file": uploaded_file,
            },
            format="multipart",
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 1)

    def test_session_file_upload_still_requires_csrf(self):
        uploaded_file = SimpleUploadedFile(
            "prescription.pdf",
            b"demo prescription file",
            content_type="application/pdf",
        )
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.patient)

        response = client.post(
            reverse("send-message"),
            {
                "recipient": self.doctor.pk,
                "message_type": "file",
                "file": uploaded_file,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Message.objects.exists())

    def test_unassigned_contact_cannot_be_messaged_or_read(self):
        self.client.force_authenticate(user=self.other_patient)

        send_response = self.client.post(
            reverse("send-message"),
            {
                "recipient": self.doctor.pk,
                "message_type": "text",
                "content": "Not assigned.",
            },
            format="json",
        )
        list_response = self.client.get(
            reverse("message-thread", args=[self.doctor.pk])
        )

        self.assertEqual(send_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(list_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Message.objects.exists())

    def test_chat_page_renders_bootstrap_context(self):
        self.client.force_login(self.patient)

        response = self.client.get(reverse("chat-room"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "const chatContext = JSON.parse")
        self.assertContains(response, "chat-patient")
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertContains(response, 'id="upload-status"')
        self.assertContains(response, "Upload failed. Your file is still selected; you can retry.")


class ChatConsumerTests(TransactionTestCase):
    def setUp(self):
        self.doctor = User.objects.create_user(
            username="ws-doctor",
            password="test-password",
            role="doctor",
            first_name="Web",
            last_name="Doctor",
        )
        self.patient = User.objects.create_user(
            username="ws-patient",
            password="test-password",
            role="patient",
            first_name="Web",
            last_name="Patient",
        )
        self.unrelated_patient = User.objects.create_user(
            username="unrelated-patient",
            password="test-password",
            role="patient",
        )
        self.patient_profile = self.patient.patient_profile
        self.doctor.doctor_profile.patients.add(self.patient_profile)
        self.doctor_token = str(RefreshToken.for_user(self.doctor).access_token)
        self.patient_token = str(RefreshToken.for_user(self.patient).access_token)
        self.unrelated_patient_token = str(
            RefreshToken.for_user(self.unrelated_patient).access_token
        )

    def test_chat_broadcasts_messages_and_read_receipts(self):
        async_to_sync(self._test_chat_broadcasts_messages_and_read_receipts)()

    async def _test_chat_broadcasts_messages_and_read_receipts(self):
        patient_socket = WebsocketCommunicator(
            application,
            f"/ws/chat/{self.doctor.pk}/",
            subprotocols=["jwt", self.patient_token],
            headers=[(b"origin", b"http://localhost"), (b"host", b"localhost")],
        )
        doctor_socket = WebsocketCommunicator(
            application,
            f"/ws/chat/{self.patient.pk}/",
            subprotocols=["jwt", self.doctor_token],
            headers=[(b"origin", b"http://localhost"), (b"host", b"localhost")],
        )
        patient_connected, _ = await patient_socket.connect()
        doctor_connected, _ = await doctor_socket.connect()
        self.assertTrue(patient_connected)
        self.assertTrue(doctor_connected)

        await patient_socket.send_json_to(
            {"type": "chat_message", "content": "Can you help me?"}
        )
        patient_event = await patient_socket.receive_json_from()
        doctor_event = await doctor_socket.receive_json_from()
        self.assertEqual(patient_event, doctor_event)
        self.assertEqual(patient_event["type"], "chat_message")
        self.assertEqual(patient_event["message"]["content"], "Can you help me?")
        self.assertEqual(patient_event["message"]["sender"], self.patient.pk)

        await doctor_socket.send_json_to({"type": "read_messages"})
        patient_receipt = await patient_socket.receive_json_from()
        doctor_receipt = await doctor_socket.receive_json_from()
        self.assertEqual(patient_receipt, doctor_receipt)
        self.assertEqual(patient_receipt["type"], "read_receipt")
        self.assertEqual(len(patient_receipt["message_ids"]), 1)

        await patient_socket.disconnect()
        await doctor_socket.disconnect()

        message = await self.get_message()
        self.assertTrue(message.is_read)

    async def get_message(self):
        return await Message.objects.aget()

    def test_websocket_rejects_missing_token(self):
        async_to_sync(self._test_websocket_rejects_missing_token)()

    async def _test_websocket_rejects_missing_token(self):
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/{self.doctor.pk}/",
            headers=[(b"origin", b"http://localhost"), (b"host", b"localhost")],
        )

        connected, _ = await communicator.connect()

        self.assertFalse(connected)

    def test_websocket_rejects_unassigned_contact(self):
        async_to_sync(self._test_websocket_rejects_unassigned_contact)()

    async def _test_websocket_rejects_unassigned_contact(self):
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/{self.doctor.pk}/",
            subprotocols=["jwt", self.unrelated_patient_token],
            headers=[(b"origin", b"http://localhost"), (b"host", b"localhost")],
        )

        connected, close_code = await communicator.connect()

        self.assertFalse(connected)
        self.assertEqual(close_code, 4403)
