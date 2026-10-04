from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils import timezone

from apps.accounts.models import AdvocateProfile


private_verification_storage = FileSystemStorage(
    location=settings.PRIVATE_MEDIA_ROOT / "verification_evidence"
)


def verification_upload_path(instance: "VerificationDocument", filename: str) -> str:
    """Keep a generated storage path separate from the original filename."""
    suffix = Path(filename).suffix.lower()
    return f"{instance.application_id}/{uuid4().hex}{suffix}"


def validate_verification_file(uploaded_file) -> None:
    allowed_extensions = {".pdf", ".jpg", ".jpeg", ".png"}
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in allowed_extensions:
        raise ValidationError("Upload a PDF, JPG, JPEG, or PNG file.")
    if uploaded_file.size > settings.MAX_VERIFICATION_UPLOAD_BYTES:
        raise ValidationError("The file is larger than the permitted upload size.")


class VerificationEvidenceType(models.Model):
    """Configurable evidence requirements; this model contains no legal policy claims."""

    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    is_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("display_order", "name")

    def __str__(self) -> str:
        return self.name


class VerificationApplication(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        UNDER_REVIEW = "UNDER_REVIEW", "Under review"
        VERIFIED = "VERIFIED", "Verified"
        NEEDS_MORE_INFORMATION = "NEEDS_MORE_INFORMATION", "Needs more information"
        REJECTED = "REJECTED", "Rejected"
        SUSPENDED = "SUSPENDED", "Suspended"
        REVOKED = "REVOKED", "Revoked"

    profile = models.ForeignKey(
        AdvocateProfile, on_delete=models.CASCADE, related_name="verification_applications"
    )
    public_id = models.UUIDField(default=uuid4, unique=True, editable=False)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.DRAFT)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateField(null=True, blank=True)
    policy_version = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    @property
    def is_expired(self) -> bool:
        return bool(self.expires_at and self.expires_at < timezone.localdate())

    @property
    def can_edit_evidence(self) -> bool:
        return self.status in {self.Status.DRAFT, self.Status.NEEDS_MORE_INFORMATION}

    def required_evidence_is_present(self) -> bool:
        required_ids = self.required_evidence_types().values_list("id", flat=True)
        uploaded_ids = self.documents.exclude(
            scan_status=VerificationDocument.ScanStatus.REPLACED
        ).values_list("evidence_type_id", flat=True)
        return set(required_ids).issubset(set(uploaded_ids))

    def required_evidence_types(self):
        return VerificationEvidenceType.objects.filter(is_active=True, is_required=True)

    def required_evidence_is_safe(self) -> bool:
        required_ids = set(self.required_evidence_types().values_list("id", flat=True))
        if not required_ids:
            return False
        safe_ids = set(
            self.documents.filter(scan_status=VerificationDocument.ScanStatus.CLEAN)
            .exclude(scan_status=VerificationDocument.ScanStatus.REPLACED)
            .values_list("evidence_type_id", flat=True)
        )
        return required_ids.issubset(safe_ids)

    def submit(self, actor) -> None:
        if self.status not in {self.Status.DRAFT, self.Status.NEEDS_MORE_INFORMATION}:
            raise ValidationError("This verification application cannot be submitted now.")
        if not self.required_evidence_is_present():
            raise ValidationError("Upload every currently required evidence type before submitting.")
        self.transition(self.Status.SUBMITTED, actor=actor, comment="Application submitted by advocate.")

    def transition(self, new_status: str, *, actor, comment: str = "", expires_at=None) -> None:
        allowed = {
            self.Status.DRAFT: {self.Status.SUBMITTED},
            self.Status.SUBMITTED: {
                self.Status.UNDER_REVIEW,
                self.Status.NEEDS_MORE_INFORMATION,
                self.Status.VERIFIED,
                self.Status.REJECTED,
            },
            self.Status.UNDER_REVIEW: {
                self.Status.NEEDS_MORE_INFORMATION,
                self.Status.VERIFIED,
                self.Status.REJECTED,
            },
            self.Status.NEEDS_MORE_INFORMATION: {self.Status.SUBMITTED},
            self.Status.VERIFIED: {self.Status.SUSPENDED, self.Status.REVOKED},
            self.Status.SUSPENDED: {self.Status.VERIFIED, self.Status.REVOKED},
        }
        if new_status not in allowed.get(self.status, set()):
            raise ValidationError("This verification status transition is not allowed.")
        if new_status == self.Status.VERIFIED and not self.required_evidence_is_safe():
            raise ValidationError(
                "Verification cannot be approved until configured required evidence is security-cleared."
            )
        comment_required = {
            self.Status.NEEDS_MORE_INFORMATION,
            self.Status.REJECTED,
            self.Status.SUSPENDED,
            self.Status.REVOKED,
        }
        if new_status in comment_required and not comment.strip():
            raise ValidationError("A reason or comment is required for this decision.")

        previous_status = self.status
        self.status = new_status
        now = timezone.now()
        update_fields = ["status", "updated_at"]
        if new_status == self.Status.SUBMITTED:
            self.submitted_at = now
            update_fields.append("submitted_at")
        if new_status not in {self.Status.DRAFT, self.Status.SUBMITTED}:
            self.reviewed_at = now
            update_fields.append("reviewed_at")
        if expires_at is not None:
            self.expires_at = expires_at
            update_fields.append("expires_at")
        self.save(update_fields=update_fields)

        self.profile.verification_status = new_status
        self.profile.save(update_fields=["verification_status", "updated_at"])
        VerificationReviewEvent.objects.create(
            application=self,
            actor=actor,
            from_status=previous_status,
            to_status=new_status,
            comment=comment.strip(),
        )

    def __str__(self) -> str:
        return f"{self.profile} — {self.get_status_display()}"


class VerificationDocument(models.Model):
    class ScanStatus(models.TextChoices):
        PENDING = "PENDING", "Pending security scan"
        CLEAN = "CLEAN", "Security scan passed"
        REJECTED = "REJECTED", "Rejected as unsafe"
        REPLACED = "REPLACED", "Replaced"

    public_id = models.UUIDField(default=uuid4, unique=True, editable=False)
    application = models.ForeignKey(
        VerificationApplication, on_delete=models.CASCADE, related_name="documents"
    )
    evidence_type = models.ForeignKey(
        VerificationEvidenceType, on_delete=models.PROTECT, related_name="documents"
    )
    original_filename = models.CharField(max_length=255)
    file = models.FileField(storage=private_verification_storage, upload_to=verification_upload_path)
    byte_size = models.PositiveBigIntegerField()
    scan_status = models.CharField(
        max_length=16, choices=ScanStatus.choices, default=ScanStatus.PENDING
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    replaced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-uploaded_at",)

    def mark_replaced(self) -> None:
        self.scan_status = self.ScanStatus.REPLACED
        self.replaced_at = timezone.now()
        self.save(update_fields=["scan_status", "replaced_at"])

    @property
    def is_available_for_download(self) -> bool:
        return self.scan_status == self.ScanStatus.CLEAN

    def __str__(self) -> str:
        return f"{self.evidence_type}: {self.original_filename}"


class VerificationReviewEvent(models.Model):
    application = models.ForeignKey(
        VerificationApplication, on_delete=models.CASCADE, related_name="review_events"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="verification_review_events"
    )
    from_status = models.CharField(max_length=32)
    to_status = models.CharField(max_length=32)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)


class VerificationDocumentAccessEvent(models.Model):
    document = models.ForeignKey(VerificationDocument, on_delete=models.CASCADE)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=32, default="DOWNLOADED")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
