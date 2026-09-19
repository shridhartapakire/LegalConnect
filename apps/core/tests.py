from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class PublicFoundationTests(TestCase):
    def test_landing_page_and_health_endpoint_are_available(self) -> None:
        home = self.client.get(reverse("core:home"))
        health = self.client.get(reverse("core:health"))

        self.assertEqual(home.status_code, 200)
        self.assertContains(home, "Legal Connect")
        self.assertEqual(health.status_code, 200)
        self.assertJSONEqual(health.content, {"status": "ok"})

    def test_unauthenticated_dashboard_redirects_to_login(self) -> None:
        response = self.client.get(reverse("core:client_dashboard"))

        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('core:client_dashboard')}")


class RoleAccessTests(TestCase):
    def setUp(self) -> None:
        self.client_user = User.objects.create_user(
            email="client@example.com", password="safe-password-123", primary_role="CLIENT"
        )
        self.advocate_user = User.objects.create_user(
            email="advocate@example.com", password="safe-password-123", primary_role="ADVOCATE"
        )

    def test_client_can_access_client_dashboard_not_advocate_dashboard(self) -> None:
        self.client.force_login(self.client_user)

        self.assertEqual(self.client.get(reverse("core:client_dashboard")).status_code, 200)
        self.assertEqual(self.client.get(reverse("core:advocate_dashboard")).status_code, 403)

    def test_advocate_can_access_advocate_dashboard_not_client_dashboard(self) -> None:
        self.client.force_login(self.advocate_user)

        self.assertEqual(self.client.get(reverse("core:advocate_dashboard")).status_code, 200)
        self.assertEqual(self.client.get(reverse("core:client_dashboard")).status_code, 403)
