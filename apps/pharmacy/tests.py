from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import Order, Payment, PharmacyItem


User = get_user_model()


class PharmacyAccessTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="pharmacy-user", password="test-pass")
        self.other_user = User.objects.create_user(
            username="other-pharmacy-user",
            password="test-pass",
        )
        self.order = Order.objects.create(user=self.user, total_price=Decimal("125.00"))
        self.other_order = Order.objects.create(
            user=self.other_user,
            total_price=Decimal("200.00"),
        )
        self.payment = Payment.objects.create(
            order=self.order,
            amount=Decimal("125.00"),
            transaction_id="OWN-TRANSACTION",
        )
        self.other_payment = Payment.objects.create(
            order=self.other_order,
            amount=Decimal("200.00"),
            transaction_id="OTHER-TRANSACTION",
        )
        self.client = APIClient()

    def test_orders_are_scoped_to_the_authenticated_user(self):
        self.client.force_authenticate(user=self.user)

        list_response = self.client.get(reverse("pharmacy:order-list"))
        detail_response = self.client.get(
            reverse("pharmacy:order-detail", args=[self.other_order.pk])
        )

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]["id"], self.order.pk)
        self.assertEqual(detail_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_payments_are_read_only_and_scoped_to_the_order_owner(self):
        self.client.force_authenticate(user=self.user)

        list_response = self.client.get(reverse("pharmacy:payment-list"))
        detail_response = self.client.get(
            reverse("pharmacy:payment-detail", args=[self.other_payment.pk])
        )
        create_response = self.client.post(
            reverse("pharmacy:payment-list"),
            {
                "order": self.order.pk,
                "amount": "125.00",
                "transaction_id": "FORGED-TRANSACTION",
            },
            format="json",
        )

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(detail_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(create_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(Payment.objects.count(), 2)

    def test_non_staff_users_cannot_manage_pharmacy_inventory(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("pharmacy:pharmacy-item-list"),
            {"name": "Medicine", "price": "25.00", "stock": 10},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(PharmacyItem.objects.exists())
