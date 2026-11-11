from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import Notification


User = get_user_model()


class NotificationApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="notification-user", password="test-pass")
        self.other_user = User.objects.create_user(
            username="other-notification-user",
            password="test-pass",
        )
        self.notification = Notification.objects.create(
            user=self.user,
            message="Your appointment is tomorrow.",
        )
        self.other_notification = Notification.objects.create(
            user=self.other_user,
            message="Private notification.",
        )
        self.client = APIClient()

    def test_list_only_returns_authenticated_users_notifications(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("notification-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.notification.pk)

    def test_user_can_mark_own_notification_read(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("notification-read", args=[self.notification.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_user_cannot_mark_another_users_notification_read(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("notification-read", args=[self.other_notification.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.other_notification.refresh_from_db()
        self.assertFalse(self.other_notification.is_read)
