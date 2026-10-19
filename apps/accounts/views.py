from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from .forms import AdvocateProfileForm, ClientProfileForm, LoginForm, RegistrationForm
from .models import AdvocateProfile, User


class LegalConnectLoginView(LoginView):
    authentication_form = LoginForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


def register(request: HttpRequest, role: str) -> HttpResponse:
    """Create a client or advocate account from an explicit registration route."""
    allowed_roles = {choice.value for choice in User.PrimaryRole}
    if role not in allowed_roles:
        return redirect("core:home")

    if request.user.is_authenticated:
        return redirect("core:dashboard_redirect")

    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(primary_role=role)
        login(request, user)
        messages.success(request, "Your account has been created.")
        return redirect("core:dashboard_redirect")

    role_label = User.PrimaryRole(role).label
    return render(
        request,
        "accounts/register.html",
        {"form": form, "role": role, "role_label": role_label},
    )


@login_required
def edit_advocate_profile(request: HttpRequest) -> HttpResponse:
    if not request.user.is_advocate:
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied("Only advocate accounts can edit an advocate profile.")
    profile = request.user.advocate_profile
    form = AdvocateProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your professional profile has been saved.")
        return redirect("accounts:edit_advocate_profile")
    return render(request, "accounts/advocate_profile_form.html", {"form": form, "profile": profile})


@login_required
def edit_client_profile(request: HttpRequest) -> HttpResponse:
    """Allow a client to edit only the profile attached to their account."""
    if not request.user.is_client:
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied("Only client accounts can edit a client profile.")
    profile = request.user.client_profile
    form = ClientProfileForm(request.POST or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your client profile has been saved.")
        return redirect("accounts:edit_client_profile")
    return render(request, "accounts/client_profile_form.html", {"form": form, "profile": profile})


@login_required
def mark_profile_ready(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return redirect("accounts:edit_advocate_profile")
    if not request.user.is_advocate:
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied("Only advocate accounts can update an advocate profile.")
    try:
        request.user.advocate_profile.mark_ready_for_review()
    except ValidationError as error:
        messages.error(request, error.messages[0])
    else:
        messages.success(request, "Your profile is ready for publication once verification is complete.")
    return redirect("core:advocate_dashboard")


@login_required
def publish_profile(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return redirect("core:advocate_dashboard")
    if not request.user.is_advocate:
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied("Only advocate accounts can publish an advocate profile.")
    try:
        request.user.advocate_profile.publish()
    except ValidationError as error:
        messages.error(request, error.messages[0])
    else:
        messages.success(request, "Your professional profile is now publicly visible.")
    return redirect("core:advocate_dashboard")


def public_advocate_profile(request: HttpRequest, public_id) -> HttpResponse:
    profile = get_object_or_404(AdvocateProfile, public_id=public_id)
    if not profile.is_publicly_visible:
        raise Http404("This advocate profile is not publicly available.")
    return render(request, "accounts/public_advocate_profile.html", {"profile": profile})


def public_advocate_photo(request: HttpRequest, public_id) -> FileResponse:
    profile = get_object_or_404(AdvocateProfile, public_id=public_id)
    if not profile.is_publicly_visible or not profile.profile_photo:
        raise Http404("This profile photo is not publicly available.")
    return FileResponse(profile.profile_photo.open("rb"), content_type="image/*")
