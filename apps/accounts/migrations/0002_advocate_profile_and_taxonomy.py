import uuid

import django.core.validators
from django.db import migrations, models


def create_initial_taxonomies(apps, schema_editor):
    PracticeArea = apps.get_model("accounts", "PracticeArea")
    Language = apps.get_model("accounts", "Language")
    Locality = apps.get_model("accounts", "Locality")
    practice_areas = (
        "Civil", "Criminal", "Family", "Property", "Consumer", "Cyber",
        "Employment", "Corporate", "Intellectual Property", "Motor Vehicle", "Other",
    )
    for order, name in enumerate(practice_areas):
        PracticeArea.objects.get_or_create(
            name=name,
            defaults={"slug": name.lower().replace(" ", "-"), "display_order": order},
        )
    for order, (name, code) in enumerate(
        (("Kannada", "kn"), ("Marathi", "mr"), ("Hindi", "hi"), ("English", "en"))
    ):
        Language.objects.get_or_create(name=name, defaults={"code": code, "display_order": order})
    Locality.objects.get_or_create(
        name="Chikodi", defaults={"district_or_region": "Belagavi district", "display_order": 0}
    )


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="Language",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True)),
                ("code", models.CharField(max_length=12, unique=True)),
                ("is_active", models.BooleanField(default=True)),
                ("display_order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={"ordering": ("display_order", "name")},
        ),
        migrations.CreateModel(
            name="Locality",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("district_or_region", models.CharField(blank=True, max_length=120)),
                ("is_active", models.BooleanField(default=True)),
                ("display_order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={"ordering": ("display_order", "name")},
        ),
        migrations.CreateModel(
            name="PracticeArea",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("slug", models.SlugField(blank=True, max_length=120, unique=True)),
                ("is_active", models.BooleanField(default=True)),
                ("display_order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={"ordering": ("display_order", "name")},
        ),
        migrations.AddField(model_name="advocateprofile", name="availability_summary", field=models.CharField(blank=True, help_text="Optional profile summary. Appointment booking is not yet available.", max_length=240)),
        migrations.AddField(model_name="advocateprofile", name="consultation_fee_display", field=models.CharField(blank=True, help_text="Optional display-only information. Legal Connect does not process payments.", max_length=100)),
        migrations.AddField(model_name="advocateprofile", name="consultation_modes", field=models.JSONField(blank=True, default=list)),
        migrations.AddField(model_name="advocateprofile", name="languages", field=models.ManyToManyField(blank=True, to="accounts.language")),
        migrations.AddField(model_name="advocateprofile", name="office_location_label", field=models.CharField(blank=True, help_text="A general professional location that may be displayed after publication.", max_length=160)),
        migrations.AddField(model_name="advocateprofile", name="private_office_address", field=models.TextField(blank=True)),
        migrations.AddField(model_name="advocateprofile", name="practice_areas", field=models.ManyToManyField(blank=True, to="accounts.practicearea")),
        migrations.AddField(model_name="advocateprofile", name="professional_headline", field=models.CharField(blank=True, max_length=180)),
        migrations.AddField(model_name="advocateprofile", name="profile_photo", field=models.FileField(blank=True, upload_to="profile_photos/")),
        migrations.AddField(model_name="advocateprofile", name="public_id", field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
        migrations.AddField(model_name="advocateprofile", name="service_areas", field=models.ManyToManyField(blank=True, to="accounts.locality")),
        migrations.AddField(model_name="advocateprofile", name="verification_status", field=models.CharField(choices=[("NOT_STARTED", "Not started"), ("DRAFT", "Draft"), ("SUBMITTED", "Submitted"), ("UNDER_REVIEW", "Under review"), ("VERIFIED", "Verified"), ("NEEDS_MORE_INFORMATION", "Needs more information"), ("REJECTED", "Rejected"), ("SUSPENDED", "Suspended"), ("REVOKED", "Revoked")], default="NOT_STARTED", max_length=32)),
        migrations.AlterField(model_name="advocateprofile", name="publication_status", field=models.CharField(choices=[("DRAFT", "Draft"), ("READY_FOR_REVIEW", "Ready for review"), ("PUBLISHED", "Published"), ("UNPUBLISHED", "Unpublished")], default="DRAFT", max_length=16)),
        migrations.AddField(model_name="advocateprofile", name="years_of_experience", field=models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0)])),
        migrations.RunPython(create_initial_taxonomies, migrations.RunPython.noop),
    ]
