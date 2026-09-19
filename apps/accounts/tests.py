from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse


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
