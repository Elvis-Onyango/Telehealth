from django.test import TestCase
from django.urls import reverse

from apps.users.models import User


class LandingPageTests(TestCase):
    def test_landing_page_renders_primary_navigation_and_calls_to_action(self):
        response = self.client.get(reverse("landing:landing_page"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Better care begins with a")
        self.assertContains(response, reverse("users:register-page"))
        self.assertContains(response, reverse("users:login-page"))
        self.assertContains(response, reverse("users:doctor-page"))

    def test_landing_page_shows_live_doctor_directory_profiles(self):
        doctor_user = User.objects.create_user(
            username="landing-doctor",
            password="Safe-Password-729!",
            first_name="Jordan",
            last_name="Care",
            role="doctor",
        )
        doctor_user.doctor_profile.specialization = "Family Medicine"
        doctor_user.doctor_profile.save(update_fields=["specialization"])

        response = self.client.get(reverse("landing:landing_page"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jordan Care")
        self.assertContains(response, "Family Medicine")
        self.assertContains(response, "doctors in the directory")
