from __future__ import annotations

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.db import models


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
    """Private profile foundation. Publication and verification come in later phases."""

    class PublicationStatus(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"
        PAUSED = "PAUSED", "Paused"

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="advocate_profile"
    )
    professional_name = models.CharField(max_length=160, blank=True)
    professional_description = models.TextField(
        blank=True, validators=[MaxLengthValidator(2_000)]
    )
    publication_status = models.CharField(
        max_length=16, choices=PublicationStatus.choices, default=PublicationStatus.DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.professional_name or self.user.email

    def clean(self) -> None:
        super().clean()
        if self.user_id and not self.user.is_advocate:
            raise ValidationError("Advocate profiles require an advocate account.")
