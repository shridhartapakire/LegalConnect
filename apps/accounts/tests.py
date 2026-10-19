from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Language, Locality


User = get_user_model()


class UserFoundationTests(TestCase):
    def test_client_user_creation_creates_client_profile(self) -> None:
        user = User.objects.create_user(
            email="client@example.com", password="safe-password-123", primary_role="CLIENT"
        )

        self.assertTrue(user.is_client)
        self.assertFalse(user.is_advocate)
        self.assertTrue(hasattr(user, "client_profile"))
        self.assertFalse(hasattr(user, "advocate_profile"))

    def test_advocate_user_creation_creates_private_advocate_profile(self) -> None:
        user = User.objects.create_user(
            email="advocate@example.com", password="safe-password-123", primary_role="ADVOCATE"
        )

        self.assertTrue(user.is_advocate)
        self.assertEqual(user.advocate_profile.publication_status, "DRAFT")

    def test_email_authentication_uses_custom_user_model(self) -> None:
        User.objects.create_user(
            email="client@example.com", password="safe-password-123", primary_role="CLIENT"
        )

        logged_in = self.client.login(email="client@example.com", password="safe-password-123")

        self.assertTrue(logged_in)

    def test_primary_role_cannot_be_changed_after_creation(self) -> None:
        user = User.objects.create_user(
            email="client@example.com", password="safe-password-123", primary_role="CLIENT"
        )
        user.primary_role = "ADVOCATE"

        with self.assertRaises(ValidationError):
            user.full_clean()


class ClientProfileTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(email="client@example.com", primary_role="CLIENT")
        self.url = reverse("accounts:edit_client_profile")
        self.language = Language.objects.get(name="Kannada")
        self.locality = Locality.objects.get(name="Chikodi")

    def test_client_can_edit_own_private_profile_with_controlled_preferences(self) -> None:
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {
                "display_name": "Client display name",
                "preferred_language": self.language.pk,
                "preferred_locality": self.locality.pk,
            },
        )

        self.assertRedirects(response, self.url)
        profile = self.user.client_profile
        profile.refresh_from_db()
        self.assertEqual(profile.display_name, "Client display name")
        self.assertEqual(profile.preferred_language, self.language)
        self.assertEqual(profile.preferred_locality, self.locality)
        self.assertEqual(profile.locality, "")

    def test_client_profile_rejects_invalid_or_inactive_taxonomy_values(self) -> None:
        inactive_language = Language.objects.create(name="Inactive language", code="inactive", is_active=False)
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {
                "display_name": "x" * 121,
                "preferred_language": inactive_language.pk,
                "preferred_locality": self.locality.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ensure this value has at most 120 characters")
        self.assertContains(response, "Select a valid choice")
        self.user.client_profile.refresh_from_db()
        self.assertEqual(self.user.client_profile.display_name, "")
        self.assertIsNone(self.user.client_profile.preferred_language)

    def test_profile_editor_requires_a_client_account(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

        advocate = User.objects.create_user(email="advocate@example.com", primary_role="ADVOCATE")
        self.client.force_login(advocate)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_client_cannot_view_or_modify_another_clients_profile(self) -> None:
        other_user = User.objects.create_user(email="other@example.com", primary_role="CLIENT")
        other_user.client_profile.display_name = "Other private client"
        other_user.client_profile.save()
        self.client.force_login(self.user)

        response = self.client.get(f"{self.url}?profile={other_user.client_profile.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Other private client")
        self.client.post(
            f"{self.url}?profile={other_user.client_profile.pk}",
            {
                "display_name": "Attempted edit",
                "preferred_language": self.language.pk,
                "preferred_locality": self.locality.pk,
            },
        )
        other_user.client_profile.refresh_from_db()
        self.assertEqual(other_user.client_profile.display_name, "Other private client")
