from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import AdvocateProfile, Language, Locality, PracticeArea
from .models import ConsultationRequest, RequestStatusEvent


User = get_user_model()


class ConsultationFactoryMixin:
    def client_user(self, email="client@example.com"):
        return User.objects.create_user(email=email, primary_role="CLIENT")

    def advocate_user(self, email="advocate@example.com", published=True):
        user = User.objects.create_user(email=email, primary_role="ADVOCATE")
        profile = user.advocate_profile
        profile.professional_name = "Advocate " + email.split("@")[0]
        profile.professional_headline = "Civil law practitioner"
        profile.professional_description = "Professional profile for directory and request tests."
        profile.years_of_experience = 5
        profile.consultation_modes = ["IN_PERSON", "PHONE"]
        profile.verification_status = AdvocateProfile.VerificationStatus.VERIFIED if published else AdvocateProfile.VerificationStatus.NOT_STARTED
        profile.publication_status = AdvocateProfile.PublicationStatus.PUBLISHED if published else AdvocateProfile.PublicationStatus.DRAFT
        profile.save()
        profile.practice_areas.add(PracticeArea.objects.get(name="Civil"))
        profile.languages.add(Language.objects.get(name="Kannada"))
        profile.service_areas.add(Locality.objects.get(name="Chikodi"))
        return user

    def submitted_request(self, client=None, advocate=None):
        client = client or self.client_user()
        advocate = advocate or self.advocate_user()
        obj = ConsultationRequest.objects.create(
            client=client.client_profile, advocate=advocate.advocate_profile,
            status=ConsultationRequest.Status.SUBMITTED, subject="Property dispute consultation",
            description="I would like an initial consultation about a property dispute.",
            practice_area=PracticeArea.objects.get(name="Civil"), preferred_mode="PHONE",
            preferred_locality=Locality.objects.get(name="Chikodi"),
        )
        return obj


class DirectoryTests(ConsultationFactoryMixin, TestCase):
    def test_directory_shows_only_published_verified_complete_profiles(self):
        public_user = self.advocate_user("visible@example.com")
        hidden_user = self.advocate_user("hidden@example.com", published=False)
        incomplete_user = self.advocate_user("incomplete@example.com")
        incomplete_user.advocate_profile.languages.clear()

        response = self.client.get(reverse("consultations:directory"))

        self.assertContains(response, public_user.advocate_profile.professional_name)
        self.assertNotContains(response, hidden_user.advocate_profile.professional_name)
        self.assertNotContains(response, incomplete_user.advocate_profile.professional_name)

    def test_directory_filters_by_taxonomy_mode_and_search(self):
        user = self.advocate_user("matching@example.com")
        user.advocate_profile.professional_headline = "Family and civil matters"
        user.advocate_profile.save()
        response = self.client.get(reverse("consultations:directory"), {"q": "Family", "practice_area": PracticeArea.objects.get(name="Civil").pk, "language": Language.objects.get(name="Kannada").pk, "locality": Locality.objects.get(name="Chikodi").pk, "mode": "PHONE", "sort": "experience"})
        self.assertContains(response, user.advocate_profile.professional_name)

    def test_directory_paginates_eligible_profiles(self):
        for number in range(13):
            self.advocate_user(f"page-{number}@example.com")

        first_page = self.client.get(reverse("consultations:directory"))
        second_page = self.client.get(reverse("consultations:directory"), {"page": 2})

        self.assertEqual(first_page.context["page_obj"].paginator.count, 13)
        self.assertEqual(first_page.context["page_obj"].number, 1)
        self.assertEqual(second_page.context["page_obj"].number, 2)
        self.assertEqual(len(second_page.context["page_obj"].object_list), 1)


class ConsultationRequestTests(ConsultationFactoryMixin, TestCase):
    def setUp(self):
        self.client_user_obj = self.client_user()
        self.advocate_user_obj = self.advocate_user()
        self.create_url = reverse("consultations:create_request", args=[self.advocate_user_obj.advocate_profile.public_id])

    def request_data(self):
        return {"subject": "Property question", "description": "I need a first consultation about a property matter.", "practice_area": PracticeArea.objects.get(name="Civil").pk, "preferred_mode": "PHONE", "preferred_locality": Locality.objects.get(name="Chikodi").pk}

    def test_client_can_submit_a_request_and_event_is_recorded(self):
        self.client.force_login(self.client_user_obj)
        response = self.client.post(self.create_url, self.request_data())
        obj = ConsultationRequest.objects.get()
        self.assertRedirects(response, reverse("consultations:client_request_detail", args=[obj.public_id]))
        self.assertEqual(obj.status, ConsultationRequest.Status.SUBMITTED)
        self.assertTrue(RequestStatusEvent.objects.filter(request=obj, to_status="SUBMITTED", actor=self.client_user_obj).exists())

    def test_non_client_cannot_submit_and_unpublished_advocate_cannot_be_targeted(self):
        self.client.force_login(self.advocate_user_obj)
        self.assertEqual(self.client.get(self.create_url).status_code, 403)
        hidden = self.advocate_user("hidden@example.com", published=False)
        self.client.force_login(self.client_user_obj)
        self.assertEqual(self.client.get(reverse("consultations:create_request", args=[hidden.advocate_profile.public_id])).status_code, 404)

    def test_client_cannot_read_or_withdraw_someone_elses_request(self):
        other_client = self.client_user("other@example.com")
        obj = self.submitted_request(client=other_client, advocate=self.advocate_user_obj)
        self.client.force_login(self.client_user_obj)
        self.assertEqual(self.client.get(reverse("consultations:client_request_detail", args=[obj.public_id])).status_code, 404)
        self.assertEqual(self.client.post(reverse("consultations:withdraw_request", args=[obj.public_id])).status_code, 404)

    def test_client_can_withdraw_submitted_request(self):
        obj = self.submitted_request(client=self.client_user_obj, advocate=self.advocate_user_obj)
        self.client.force_login(self.client_user_obj)
        self.client.post(reverse("consultations:withdraw_request", args=[obj.public_id]))
        obj.refresh_from_db()
        self.assertEqual(obj.status, ConsultationRequest.Status.WITHDRAWN)
        self.assertTrue(obj.status_events.filter(to_status="WITHDRAWN").exists())

    def test_only_own_advocate_can_review_request(self):
        obj = self.submitted_request(client=self.client_user_obj, advocate=self.advocate_user_obj)
        other_advocate = self.advocate_user("otheradvocate@example.com")
        self.client.force_login(other_advocate)
        self.assertEqual(self.client.get(reverse("consultations:advocate_request_detail", args=[obj.public_id])).status_code, 404)
        self.assertEqual(self.client.post(reverse("consultations:accept_request", args=[obj.public_id])).status_code, 404)

    def test_advocate_can_start_review_and_accept(self):
        obj = self.submitted_request(client=self.client_user_obj, advocate=self.advocate_user_obj)
        self.client.force_login(self.advocate_user_obj)
        self.client.post(reverse("consultations:start_review", args=[obj.public_id]))
        obj.refresh_from_db()
        self.assertEqual(obj.status, ConsultationRequest.Status.UNDER_REVIEW)
        self.client.post(reverse("consultations:accept_request", args=[obj.public_id]))
        obj.refresh_from_db()
        self.assertEqual(obj.status, ConsultationRequest.Status.ACCEPTED)
        self.assertTrue(obj.status_events.filter(to_status="ACCEPTED", actor=self.advocate_user_obj).exists())

    def test_decline_requires_reason_and_records_it(self):
        obj = self.submitted_request(client=self.client_user_obj, advocate=self.advocate_user_obj)
        self.client.force_login(self.advocate_user_obj)
        response = self.client.post(reverse("consultations:decline_request", args=[obj.public_id]), {"reason": ""})
        obj.refresh_from_db()
        self.assertEqual(obj.status, ConsultationRequest.Status.SUBMITTED)
        self.assertEqual(response.status_code, 302)
        self.client.post(reverse("consultations:decline_request", args=[obj.public_id]), {"reason": "Outside my current practice capacity."})
        obj.refresh_from_db()
        self.assertEqual(obj.status, ConsultationRequest.Status.DECLINED)
        self.assertEqual(obj.decline_reason, "Outside my current practice capacity.")

    def test_request_form_restricts_practice_area_to_advocate_profile(self):
        other_area = PracticeArea.objects.create(name="Special test practice area")
        self.client.force_login(self.client_user_obj)
        data = self.request_data(); data["practice_area"] = other_area.pk
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ConsultationRequest.objects.count(), 0)
