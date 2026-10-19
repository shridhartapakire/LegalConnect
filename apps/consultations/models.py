from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.accounts.models import AdvocateProfile, ClientProfile, Locality, PracticeArea


class ConsultationRequest(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        UNDER_REVIEW = "UNDER_REVIEW", "Under review"
        ACCEPTED = "ACCEPTED", "Accepted"
        DECLINED = "DECLINED", "Declined"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"
        EXPIRED = "EXPIRED", "Expired"
        CLOSED = "CLOSED", "Closed"

    class Mode(models.TextChoices):
        IN_PERSON = "IN_PERSON", "In-person"
        PHONE = "PHONE", "Phone"

    public_id = models.UUIDField(default=uuid4, unique=True, editable=False)
    client = models.ForeignKey(ClientProfile, on_delete=models.PROTECT, related_name="consultation_requests")
    advocate = models.ForeignKey(AdvocateProfile, on_delete=models.PROTECT, related_name="consultation_requests")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    subject = models.CharField(max_length=160)
    description = models.TextField(max_length=4000)
    practice_area = models.ForeignKey(PracticeArea, on_delete=models.PROTECT)
    preferred_mode = models.CharField(max_length=16, choices=Mode.choices)
    preferred_locality = models.ForeignKey(Locality, null=True, blank=True, on_delete=models.SET_NULL)
    submitted_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    decline_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)
        indexes = [
            models.Index(fields=("client", "status"), name="consultatio_client__4d1f19_idx"),
            models.Index(fields=("advocate", "status"), name="consultatio_advocat_777a7a_idx"),
        ]

    def transition(self, status, actor, reason=""):
        allowed = {
            self.Status.SUBMITTED: {self.Status.UNDER_REVIEW, self.Status.ACCEPTED, self.Status.DECLINED, self.Status.WITHDRAWN, self.Status.EXPIRED},
            self.Status.UNDER_REVIEW: {self.Status.ACCEPTED, self.Status.DECLINED, self.Status.WITHDRAWN, self.Status.EXPIRED},
            self.Status.ACCEPTED: {self.Status.CLOSED},
        }
        if status not in allowed.get(self.status, set()):
            raise ValidationError("This request status change is not allowed.")
        if status == self.Status.DECLINED and not reason.strip():
            raise ValidationError("A reason is required when declining a consultation request.")
        old = self.status
        self.status = status
        fields = ["status", "updated_at"]
        if status in {self.Status.ACCEPTED, self.Status.DECLINED}:
            self.responded_at = timezone.now(); fields.append("responded_at")
        if status == self.Status.DECLINED:
            self.decline_reason = reason.strip(); fields.append("decline_reason")
        if status == self.Status.CLOSED:
            self.closed_at = timezone.now(); fields.append("closed_at")
        self.save(update_fields=fields)
        RequestStatusEvent.objects.create(request=self, actor=actor, from_status=old, to_status=status, reason=reason.strip())


class RequestStatusEvent(models.Model):
    request = models.ForeignKey(ConsultationRequest, on_delete=models.CASCADE, related_name="status_events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
