from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password

from .models import AdvocateProfile, Language, Locality, PracticeArea, User


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={"autocomplete": "email", "autofocus": True}),
    )
    password = forms.CharField(
        label="Password", strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "current-password"})
    )


class RegistrationForm(forms.Form):
    email = forms.EmailField(label="Email address")
    password1 = forms.CharField(
        label="Password", strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "new-password"})
    )
    password2 = forms.CharField(
        label="Confirm password", strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "new-password"})
    )

    def clean_email(self) -> str:
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account already exists for this email address.")
        return email

    def clean(self) -> dict[str, object]:
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "The passwords do not match.")
        if password1:
            validate_password(password1)
        return cleaned_data

    def save(self, *, primary_role: str) -> User:
        return User.objects.create_user(
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
            primary_role=primary_role,
        )


class AdvocateProfileForm(forms.ModelForm):
    consultation_modes = forms.MultipleChoiceField(
        choices=AdvocateProfile.ConsultationMode.choices,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Consultation modes",
    )

    class Meta:
        model = AdvocateProfile
        fields = (
            "profile_photo",
            "professional_name",
            "professional_headline",
            "professional_description",
            "years_of_experience",
            "practice_areas",
            "languages",
            "service_areas",
            "consultation_modes",
            "office_location_label",
            "private_office_address",
            "consultation_fee_display",
            "availability_summary",
        )
        widgets = {
            "professional_description": forms.Textarea(attrs={"rows": 5}),
            "private_office_address": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["practice_areas"].queryset = PracticeArea.objects.filter(is_active=True)
        self.fields["languages"].queryset = Language.objects.filter(is_active=True)
        self.fields["service_areas"].queryset = Locality.objects.filter(is_active=True)
        self.fields["private_office_address"].help_text = "Private. This is never shown on a public profile."

    def clean_profile_photo(self):
        photo = self.cleaned_data.get("profile_photo")
        if not photo:
            return photo
        from pathlib import Path

        if Path(photo.name).suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            raise forms.ValidationError("Upload a JPG, JPEG, or PNG profile photo.")
        if photo.size > 5 * 1024 * 1024:
            raise forms.ValidationError("The profile photo must be 5 MB or smaller.")
        return photo
