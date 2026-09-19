from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password

from .models import User


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
