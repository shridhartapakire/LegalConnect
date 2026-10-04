from __future__ import annotations

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify
from uuid import uuid4


class UserManager(BaseUserManager):
    """Create users with email as the login identifier."""

    def create_user(
        self,
        email: str,
        password: str | None = None,
        *,
        primary_role: str = "CLIENT",
        **extra_fields: object,
    ) -> "User":
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, primary_role=primary_role, **extra_fields)
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email: str, password: str | None = None, **extra_fields: object
    ) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("primary_role", User.PrimaryRole.CLIENT)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """One account with one primary public service role.

    Staff permissions are provided by Django permissions/groups and do not make
    an account a public advocate or client profile.
    """

    class PrimaryRole(models.TextChoices):
        CLIENT = "CLIENT", "Client"
        ADVOCATE = "ADVOCATE", "Advocate"

    email = models.EmailField(unique=True)
    primary_role = models.CharField(max_length=16, choices=PrimaryRole.choices)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        ordering = ["email"]

    @property
    def is_client(self) -> bool:
        return self.primary_role == self.PrimaryRole.CLIENT

    @property
    def is_advocate(self) -> bool:
        return self.primary_role == self.PrimaryRole.ADVOCATE

    def __str__(self) -> str:
        return self.email

    def clean(self) -> None:
        super().clean()
        if not self.pk:
            return
        original_role = (
            type(self).objects.filter(pk=self.pk).values_list("primary_role", flat=True).first()
        )
        if original_role and original_role != self.primary_role:
            raise ValidationError(
                {"primary_role": "An account's primary role cannot be changed after creation."}
            )


class ClientProfile(models.Model):
    """Minimal private client profile; collect additional data only when needed."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="client_profile"
    )
    display_name = models.CharField(max_length=120, blank=True)
    locality = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.display_name or self.user.email

    def clean(self) -> None:
        super().clean()
        if self.user_id and not self.user.is_client:
            raise ValidationError("Client profiles require a client account.")


class AdvocateProfile(models.Model):
    """Professional profile with strictly separated private/public fields."""

    class PublicationStatus(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        READY_FOR_REVIEW = "READY_FOR_REVIEW", "Ready for review"
        PUBLISHED = "PUBLISHED", "Published"
        UNPUBLISHED = "UNPUBLISHED", "Unpublished"

    class VerificationStatus(models.TextChoices):
        NOT_STARTED = "NOT_STARTED", "Not started"
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        UNDER_REVIEW = "UNDER_REVIEW", "Under review"
        VERIFIED = "VERIFIED", "Verified"
        NEEDS_MORE_INFORMATION = "NEEDS_MORE_INFORMATION", "Needs more information"
        REJECTED = "REJECTED", "Rejected"
        SUSPENDED = "SUSPENDED", "Suspended"
        REVOKED = "REVOKED", "Revoked"

    class ConsultationMode(models.TextChoices):
        IN_PERSON = "IN_PERSON", "In-person"
        PHONE = "PHONE", "Phone"

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="advocate_profile"
    )
    professional_name = models.CharField(max_length=160, blank=True)
    public_id = models.UUIDField(default=uuid4, unique=True, editable=False)
    profile_photo = models.FileField(upload_to="profile_photos/", blank=True)
    professional_headline = models.CharField(max_length=180, blank=True)
    professional_description = models.TextField(
        blank=True, validators=[MaxLengthValidator(2_000)]
    )
    years_of_experience = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    office_location_label = models.CharField(max_length=160, blank=True, help_text="A general professional location that may be displayed after publication.")
    private_office_address = models.TextField(blank=True)
    consultation_fee_display = models.CharField(max_length=100, blank=True, help_text="Optional display-only information. Legal Connect does not process payments.")
    availability_summary = models.CharField(max_length=240, blank=True, help_text="Optional profile summary. Appointment booking is not yet available.")
    consultation_modes = models.JSONField(default=list, blank=True)
    practice_areas = models.ManyToManyField("PracticeArea", blank=True)
    languages = models.ManyToManyField("Language", blank=True)
    service_areas = models.ManyToManyField("Locality", blank=True)
    publication_status = models.CharField(
        max_length=16, choices=PublicationStatus.choices, default=PublicationStatus.DRAFT
    )
    verification_status = models.CharField(max_length=32, choices=VerificationStatus.choices, default=VerificationStatus.NOT_STARTED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.professional_name or self.user.email

    @property
    def completion_percentage(self) -> int:
        checks = [bool(self.professional_name), bool(self.professional_headline), bool(self.professional_description), self.years_of_experience is not None, self.practice_areas.exists(), self.languages.exists(), self.service_areas.exists(), bool(self.consultation_modes)]
        return round((sum(checks) / len(checks)) * 100)

    @property
    def is_complete(self) -> bool:
        return self.completion_percentage == 100

    @property
    def is_publicly_visible(self) -> bool:
        return self.publication_status == self.PublicationStatus.PUBLISHED and self.verification_status == self.VerificationStatus.VERIFIED and self.is_complete

    def mark_ready_for_review(self) -> None:
        if not self.is_complete:
            raise ValidationError("Complete all required public profile fields first.")
        self.publication_status = self.PublicationStatus.READY_FOR_REVIEW
        self.save(update_fields=["publication_status", "updated_at"])

    def publish(self) -> None:
        if not self.is_complete:
            raise ValidationError("A complete profile is required before publication.")
        if self.verification_status != self.VerificationStatus.VERIFIED:
            raise ValidationError("Only an actually verified advocate profile may be published.")
        self.publication_status = self.PublicationStatus.PUBLISHED
        self.save(update_fields=["publication_status", "updated_at"])

    def clean(self) -> None:
        super().clean()
        if self.user_id and not self.user.is_advocate:
            raise ValidationError("Advocate profiles require an advocate account.")
        allowed = {choice.value for choice in self.ConsultationMode}
        if not isinstance(self.consultation_modes, list) or not set(self.consultation_modes).issubset(allowed):
            raise ValidationError({"consultation_modes": "Select only supported consultation modes."})


class PracticeArea(models.Model):
    """Administrator-managed official practice-area taxonomy."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("display_order", "name")

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Language(models.Model):
    """Administrator-managed language taxonomy."""

    name = models.CharField(max_length=80, unique=True)
    code = models.CharField(max_length=12, unique=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("display_order", "name")

    def __str__(self) -> str:
        return self.name


class Locality(models.Model):
    """Administrator-managed locality for public service-area selection."""

    name = models.CharField(max_length=120, unique=True)
    district_or_region = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("display_order", "name")

    def __str__(self) -> str:
        return self.name
