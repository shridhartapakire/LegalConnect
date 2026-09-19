from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import LoginForm, RegistrationForm
from .models import User


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
