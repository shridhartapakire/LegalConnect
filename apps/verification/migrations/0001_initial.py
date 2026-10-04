import uuid

import apps.verification.models
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ("accounts", "0002_advocate_profile_and_taxonomy")]

    operations = [
        migrations.CreateModel(
            name="VerificationEvidenceType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("description", models.TextField(blank=True)),
                ("is_required", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("display_order", models.PositiveSmallIntegerField(default=0)),
            ], options={"ordering": ("display_order", "name")},
        ),
        migrations.CreateModel(
            name="VerificationApplication",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("status", models.CharField(choices=[("DRAFT", "Draft"), ("SUBMITTED", "Submitted"), ("UNDER_REVIEW", "Under review"), ("VERIFIED", "Verified"), ("NEEDS_MORE_INFORMATION", "Needs more information"), ("REJECTED", "Rejected"), ("SUSPENDED", "Suspended"), ("REVOKED", "Revoked")], default="DRAFT", max_length=32)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("expires_at", models.DateField(blank=True, null=True)),
                ("policy_version", models.CharField(blank=True, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="verification_applications", to="accounts.advocateprofile")),
            ], options={"ordering": ("-created_at",)},
        ),
        migrations.CreateModel(
            name="VerificationDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("original_filename", models.CharField(max_length=255)),
                ("file", models.FileField(storage=apps.verification.models.private_verification_storage, upload_to=apps.verification.models.verification_upload_path)),
                ("byte_size", models.PositiveBigIntegerField()),
                ("scan_status", models.CharField(choices=[("PENDING", "Pending security scan"), ("CLEAN", "Security scan passed"), ("REJECTED", "Rejected as unsafe"), ("REPLACED", "Replaced")], default="PENDING", max_length=16)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("replaced_at", models.DateTimeField(blank=True, null=True)),
                ("application", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="documents", to="verification.verificationapplication")),
                ("evidence_type", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="documents", to="verification.verificationevidencetype")),
            ], options={"ordering": ("-uploaded_at",)},
        ),
        migrations.CreateModel(
            name="VerificationReviewEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("from_status", models.CharField(max_length=32)),
                ("to_status", models.CharField(max_length=32)),
                ("comment", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="verification_review_events", to=settings.AUTH_USER_MODEL)),
                ("application", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="review_events", to="verification.verificationapplication")),
            ], options={"ordering": ("-created_at",)},
        ),
        migrations.CreateModel(
            name="VerificationDocumentAccessEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(default="DOWNLOADED", max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("document", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="verification.verificationdocument")),
            ], options={"ordering": ("-created_at",)},
        ),
    ]
