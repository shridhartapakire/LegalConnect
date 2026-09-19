from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET

from apps.accounts.models import User

from .decorators import role_required


def home(request: HttpRequest) -> HttpResponse:
    return render(request, "core/home.html")


@require_GET
def health(request: HttpRequest) -> JsonResponse:
    """A lightweight liveness endpoint with no sensitive system details."""
    return JsonResponse({"status": "ok"})


@login_required
def dashboard_redirect(request: HttpRequest) -> HttpResponse:
    if request.user.primary_role == User.PrimaryRole.ADVOCATE:
        return redirect("core:advocate_dashboard")
    return redirect("core:client_dashboard")


@role_required(User.PrimaryRole.CLIENT)
def client_dashboard(request: HttpRequest) -> HttpResponse:
    return render(request, "core/client_dashboard.html")


@role_required(User.PrimaryRole.ADVOCATE)
def advocate_dashboard(request: HttpRequest) -> HttpResponse:
    return render(request, "core/advocate_dashboard.html")
