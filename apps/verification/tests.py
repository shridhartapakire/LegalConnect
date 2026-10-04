from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import AdvocateProfile, Language, Locality, PracticeArea

from .models import VerificationApplication, VerificationDocument, VerificationEvidenceType


User = get_user_model()


class Phase2FactoryMixin:
    def create_advocate(self, email="advocate@example.com"):
        return User.objects.create_user(email=email, password="safe-password-123", primary_role="ADVOCATE")

    def complete_profile(self, user):
        profile = user.advocate_profile
        profile.professional_name = "Professional Advocate"
        profile.professional_headline = "Civil and family law practice"
        profile.professional_description = "Professional information supplied by this account."
        profile.years_of_experience = 5
        profile.consultation_modes = ["IN_PERSON", "PHONE"]
        profile.save()
        profile.practice_areas.add(PracticeArea.objects.get(name="Civil"))
        profile.languages.add(Language.objects.get(name="Kannada"))
        profile.service_areas.add(Locality.objects.get(name="Chikodi"))
        return profile

    def required_document(self, application, *, scan_status=VerificationDocument.ScanStatus.CLEAN):
        evidence_type = VerificationEvidenceType.objects.create(
            name="Configured professional evidence", is_required=True
        )
        return VerificationDocument.objects.create(
            application=application,
            evidence_type=evidence_type,
            original_filename="evidence.pdf",
            byte_size=4,
            scan_status=scan_status,
            file=SimpleUploadedFile("evidence.pdf", b"test", content_type="application/pdf"),
        )


class AdvocateProfileTests(Phase2FactoryMixin, TestCase):
    def test_profile_editing_assigns_admin_managed_taxonomies(self):
        user = self.create_advocate()
        self.client.force_login(user)

        response = self.client.post(
            reverse("accounts:edit_advocate_profile"),
            {
                "professional_name": "Professional Advocate",
                "professional_headline": "Civil practice",
                "professional_description": "A professional description.",
                "years_of_experience": 4,
                "practice_areas": [PracticeArea.objects.get(name="Civil").pk],
                "languages": [Language.objects.get(name="Kannada").pk],
                "service_areas": [Locality.objects.get(name="Chikodi").pk],
                "consultation_modes": ["IN_PERSON", "PHONE"],
            },
        )

        self.assertRedirects(response, reverse("accounts:edit_advocate_profile"))
        profile = user.advocate_profile
        profile.refresh_from_db()
        self.assertTrue(profile.is_complete)
        self.assertEqual(list(profile.practice_areas.values_list("name", flat=True)), ["Civil"])
        self.assertEqual(profile.consultation_modes, ["IN_PERSON", "PHONE"])

    def test_client_cannot_edit_an_advocate_profile(self):
        client_user = User.objects.create_user(
            email="client@example.com", password="safe-password-123", primary_role="CLIENT"
        )
        self.client.force_login(client_user)

        self.assertEqual(self.client.get(reverse("accounts:edit_advocate_profile")).status_code, 403)

    def test_profile_cannot_publish_until_complete_and_verified(self):
        user = self.create_advocate()
        profile = user.advocate_profile
        with self.assertRaises(ValidationError):
            profile.mark_ready_for_review()

        profile = self.complete_profile(user)
        profile.mark_ready_for_review()
        with self.assertRaises(ValidationError):
            profile.publish()

        profile.verification_status = AdvocateProfile.VerificationStatus.VERIFIED
        profile.save()
        profile.publish()
        self.assertTrue(profile.is_publicly_visible)

    def test_unpublished_profile_is_not_publicly_visible(self):
        user = self.create_advocate()
        profile = self.complete_profile(user)

        response = self.client.get(
            reverse("accounts:public_advocate_profile", args=[profile.public_id])
        )

        self.assertEqual(response.status_code, 404)

    def test_verified_published_profile_is_publicly_visible(self):
        user = self.create_advocate()
        profile = self.complete_profile(user)
        profile.verification_status = AdvocateProfile.VerificationStatus.VERIFIED
        profile.publication_status = AdvocateProfile.PublicationStatus.PUBLISHED
        profile.save()

        response = self.client.get(
            reverse("accounts:public_advocate_profile", args=[profile.public_id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Professional Advocate")


class VerificationWorkflowTests(Phase2FactoryMixin, TestCase):
    def setUp(self):
        self.advocate = self.create_advocate()
        self.staff = User.objects.create_user(
            email="staff@example.com",
            password="safe-password-123",
            primary_role="CLIENT",
            is_staff=True,
        )

    def test_advocate_can_start_and_submit_own_application(self):
        self.client.force_login(self.advocate)
        response = self.client.post(reverse("verification:start_application"))
        application = VerificationApplication.objects.get(profile=self.advocate.advocate_profile)
        self.assertRedirects(
            response, reverse("verification:application_detail", args=[application.public_id])
        )
        self.assertEqual(application.status, VerificationApplication.Status.DRAFT)
        profile = self.advocate.advocate_profile
        profile.refresh_from_db()
        self.assertEqual(profile.verification_status, "DRAFT")

        self.required_document(application)
        response = self.client.post(
            reverse("verification:submit_application", args=[application.public_id])
        )
        application.refresh_from_db()
        self.assertEqual(application.status, VerificationApplication.Status.SUBMITTED)
        self.assertEqual(response.status_code, 302)

    def test_required_evidence_prevents_submission_when_missing(self):
        application = VerificationApplication.objects.create(profile=self.advocate.advocate_profile)
        VerificationEvidenceType.objects.create(name="Required evidence", is_required=True)
        self.client.force_login(self.advocate)

        self.client.post(reverse("verification:submit_application", args=[application.public_id]))
        application.refresh_from_db()

        self.assertEqual(application.status, VerificationApplication.Status.DRAFT)

    def test_admin_approval_creates_review_history(self):
        application = VerificationApplication.objects.create(profile=self.advocate.advocate_profile)
        self.required_document(application)
        application.submit(self.advocate)
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse("verification:review_application", args=[application.public_id]),
            {"status": "VERIFIED", "comment": "Evidence meets the configured platform policy."},
        )
        application.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(application.status, VerificationApplication.Status.VERIFIED)
        self.assertEqual(application.profile.verification_status, "VERIFIED")
        self.assertTrue(application.review_events.filter(to_status="VERIFIED", actor=self.staff).exists())

    def test_rejection_requires_a_reason(self):
        application = VerificationApplication.objects.create(profile=self.advocate.advocate_profile)
        application.submit(self.advocate)
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse("verification:review_application", args=[application.public_id]),
            {"status": "REJECTED", "comment": ""},
        )
        application.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(application.status, VerificationApplication.Status.SUBMITTED)
        self.assertContains(response, "reason or comment is required")

        self.client.post(
            reverse("verification:review_application", args=[application.public_id]),
            {"status": "REJECTED", "comment": "Required information was not provided."},
        )
        application.refresh_from_db()
        self.assertEqual(application.status, VerificationApplication.Status.REJECTED)

    def test_suspension_and_revocation_require_reasons(self):
        application = VerificationApplication.objects.create(profile=self.advocate.advocate_profile)
        self.required_document(application)
        application.submit(self.advocate)
        application.transition("VERIFIED", actor=self.staff, comment="Approved.")

        with self.assertRaises(ValidationError):
            application.transition("SUSPENDED", actor=self.staff)
        application.transition("SUSPENDED", actor=self.staff, comment="Review required.")
        application.transition("REVOKED", actor=self.staff, comment="Verification revoked after review.")
        application.refresh_from_db()
        self.assertEqual(application.status, VerificationApplication.Status.REVOKED)

    def test_private_document_blocks_clients_and_other_advocates(self):
        application = VerificationApplication.objects.create(profile=self.advocate.advocate_profile)
        document = self.required_document(application)
        url = reverse("verification:download_document", args=[application.public_id, document.public_id])
        client_user = User.objects.create_user(
            email="client@example.com", password="safe-password-123", primary_role="CLIENT"
        )
        other_advocate = self.create_advocate("other@example.com")

        self.client.force_login(client_user)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(other_advocate)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.advocate)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_other_advocate_cannot_view_or_modify_an_application_by_uuid(self):
        application = VerificationApplication.objects.create(profile=self.advocate.advocate_profile)
        other_advocate = self.create_advocate("other@example.com")
        self.client.force_login(other_advocate)

        response = self.client.get(
            reverse("verification:application_detail", args=[application.public_id])
        )

        self.assertEqual(response.status_code, 404)

    def test_pending_document_is_not_downloadable_even_by_owner(self):
        application = VerificationApplication.objects.create(profile=self.advocate.advocate_profile)
        document = self.required_document(
            application, scan_status=VerificationDocument.ScanStatus.PENDING
        )
        self.client.force_login(self.advocate)

        response = self.client.get(
            reverse("verification:download_document", args=[application.public_id, document.public_id])
        )

        self.assertEqual(response.status_code, 404)

    def test_normal_user_cannot_access_staff_review_queue(self):
        self.client.force_login(self.advocate)
        response = self.client.get(reverse("verification:review_queue"))
        self.assertEqual(response.status_code, 302)
