from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.models import AdvocateProfile, Language, Locality, PracticeArea
from .forms import ConsultationRequestForm, DeclineForm
from .models import ConsultationRequest, RequestStatusEvent


def eligible_profiles():
    """Return only profiles that satisfy the complete public eligibility gate.

    The profile publication workflow already requires completion, but the
    directory also applies the rule so a direct database/admin change cannot
    accidentally make an incomplete profile discoverable.
    """
    return (
        AdvocateProfile.objects.filter(
            publication_status=AdvocateProfile.PublicationStatus.PUBLISHED,
            verification_status=AdvocateProfile.VerificationStatus.VERIFIED,
            years_of_experience__isnull=False,
            practice_areas__isnull=False,
            languages__isnull=False,
            service_areas__isnull=False,
        )
        .exclude(professional_name="")
        .exclude(professional_headline="")
        .exclude(professional_description="")
        .exclude(consultation_modes=[])
        .distinct()
        .prefetch_related("practice_areas", "languages", "service_areas")
    )


def directory(request):
    profiles = eligible_profiles()
    query = request.GET.get("q", "").strip()
    if query:
        profiles = profiles.filter(Q(professional_name__icontains=query) | Q(professional_headline__icontains=query) | Q(professional_description__icontains=query)).distinct()
    for key, relation in (("practice_area", "practice_areas"), ("language", "languages"), ("locality", "service_areas")):
        value = request.GET.get(key)
        if value: profiles = profiles.filter(**{f"{relation}__id": value})
    sort = request.GET.get("sort", "name")
    profiles = profiles.order_by("-years_of_experience", "professional_name") if sort == "experience" else profiles.order_by("professional_name")
    mode = request.GET.get("mode")
    if mode in {"IN_PERSON", "PHONE"}:
        # SQLite deliberately remains usable for local development, but does
        # not implement the PostgreSQL JSON contains lookup.
        profiles = profiles.filter(consultation_modes__contains=[mode]) if connection.vendor == "postgresql" else [profile for profile in profiles if mode in profile.consultation_modes]
    page = Paginator(profiles, 12).get_page(request.GET.get("page"))
    return render(request, "consultations/directory.html", {"page_obj": page, "practice_areas": PracticeArea.objects.filter(is_active=True), "languages": Language.objects.filter(is_active=True), "localities": Locality.objects.filter(is_active=True), "query": query})


def public_profile_or_404(public_id):
    profile = get_object_or_404(eligible_profiles(), public_id=public_id)
    if not profile.is_publicly_visible: raise Http404
    return profile


@login_required
def create_request(request, public_id):
    if not request.user.is_client: raise PermissionDenied
    advocate = public_profile_or_404(public_id)
    form = ConsultationRequestForm(advocate, request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False); obj.client = request.user.client_profile; obj.advocate = advocate; obj.status = ConsultationRequest.Status.SUBMITTED; obj.submitted_at = timezone.now(); obj.save()
        RequestStatusEvent.objects.create(request=obj, actor=request.user, from_status="DRAFT", to_status="SUBMITTED", reason="Request submitted by client.")
        messages.success(request, "Your consultation request has been submitted for advocate review.")
        return redirect("consultations:client_request_detail", request_id=obj.public_id)
    return render(request, "consultations/request_form.html", {"form": form, "advocate": advocate})


@login_required
def client_requests(request):
    if not request.user.is_client: raise PermissionDenied
    requests = ConsultationRequest.objects.filter(client=request.user.client_profile).select_related("advocate", "practice_area")
    return render(request, "consultations/client_requests.html", {"requests": requests})


@login_required
def client_request_detail(request, request_id):
    if not request.user.is_client: raise PermissionDenied
    obj = get_object_or_404(ConsultationRequest.objects.select_related("advocate", "practice_area"), public_id=request_id, client=request.user.client_profile)
    return render(request, "consultations/client_request_detail.html", {"request_obj": obj})


@login_required
@require_POST
def withdraw_request(request, request_id):
    if not request.user.is_client: raise PermissionDenied
    obj = get_object_or_404(ConsultationRequest, public_id=request_id, client=request.user.client_profile)
    try: obj.transition(ConsultationRequest.Status.WITHDRAWN, request.user, "Withdrawn by client.")
    except ValidationError as exc: messages.error(request, exc.messages[0])
    else: messages.success(request, "Consultation request withdrawn.")
    return redirect("consultations:client_request_detail", request_id=obj.public_id)


@login_required
def advocate_requests(request):
    if not request.user.is_advocate: raise PermissionDenied
    requests = ConsultationRequest.objects.filter(advocate=request.user.advocate_profile).select_related("client", "practice_area")
    return render(request, "consultations/advocate_requests.html", {"requests": requests})


@login_required
def advocate_request_detail(request, request_id):
    if not request.user.is_advocate: raise PermissionDenied
    obj = get_object_or_404(ConsultationRequest.objects.select_related("client", "practice_area", "preferred_locality"), public_id=request_id, advocate=request.user.advocate_profile)
    return render(request, "consultations/advocate_request_detail.html", {"request_obj": obj, "decline_form": DeclineForm()})


@login_required
@require_POST
def start_review(request, request_id):
    if not request.user.is_advocate:
        raise PermissionDenied
    obj = get_object_or_404(ConsultationRequest, public_id=request_id, advocate=request.user.advocate_profile)
    try:
        obj.transition(ConsultationRequest.Status.UNDER_REVIEW, request.user, "Review started by advocate.")
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    else:
        messages.success(request, "Consultation request marked as under review.")
    return redirect("consultations:advocate_request_detail", request_id=obj.public_id)


@login_required
@require_POST
def accept_request(request, request_id):
    if not request.user.is_advocate: raise PermissionDenied
    obj = get_object_or_404(ConsultationRequest, public_id=request_id, advocate=request.user.advocate_profile)
    try: obj.transition(ConsultationRequest.Status.ACCEPTED, request.user)
    except ValidationError as exc: messages.error(request, exc.messages[0])
    else: messages.success(request, "Consultation request accepted.")
    return redirect("consultations:advocate_request_detail", request_id=obj.public_id)


@login_required
@require_POST
def decline_request(request, request_id):
    if not request.user.is_advocate: raise PermissionDenied
    obj = get_object_or_404(ConsultationRequest, public_id=request_id, advocate=request.user.advocate_profile)
    form = DeclineForm(request.POST)
    if form.is_valid():
        try: obj.transition(ConsultationRequest.Status.DECLINED, request.user, form.cleaned_data["reason"])
        except ValidationError as exc: messages.error(request, exc.messages[0])
        else: messages.success(request, "Consultation request declined.")
    else: messages.error(request, "Provide a reason before declining.")
    return redirect("consultations:advocate_request_detail", request_id=obj.public_id)
