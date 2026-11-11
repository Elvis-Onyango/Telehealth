from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AdminIndexDashboardTests(TestCase):
    def test_superuser_sees_global_dashboard_with_app_navigation(self):
        user = get_user_model().objects.create_superuser(
            username="platform-admin",
            password="Safe-Password-729!",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/index.html")
        self.assertTemplateUsed(response, "admin/superadmin_base.html")
        self.assertContains(response, "Platform overview")
        self.assertContains(response, "Care network administration")
        self.assertContains(response, 'id="admin-home"')
        self.assertContains(response, 'data-admin-target="overview"')
        self.assertContains(response, "Appointments")
        self.assertContains(response, "Paid billing")
        self.assertEqual(response.context["admin_dashboard_stats"]["users"], 1)

    def test_non_superuser_staff_keeps_standard_admin_index(self):
        user = get_user_model().objects.create_user(
            username="staff-admin",
            password="Safe-Password-729!",
            is_staff=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/base_site.html")
        self.assertNotContains(response, 'id="admin-home"')
