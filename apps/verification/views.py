from __future__ import annotations

from pathlib import Path

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.models import AdvocateProfile

from .forms import VerificationDocumentUploadForm, VerificationReviewForm
from .models import (
    VerificationApplication,
    VerificationDocument,
    VerificationDocumentAccessEvent,
    VerificationReviewEvent,
)
from .services import queue_document_scan


def _advocate_profile(request: HttpRequest) -> AdvocateProfile:
    if not request.user.is_advocate:
        raise PermissionDenied("Only advocate accounts can access verification applications.")
    return request.user.advocate_profile


def _owned_application(request: HttpRequest, application_id) -> VerificationApplication:
    return get_object_or_404(
        VerificationApplication, public_id=application_id, profile=_advocate_profile(request)
    )


@login_required
@require_POST
def start_application(request: HttpRequest) -> HttpResponse:
    profile = _advocate_profile(request)
    existing = profile.verification_applications.exclude(
        status__in=[VerificationApplication.Status.REJECTED, VerificationApplication.Status.REVOKED]
    ).first()
    if existing:
        messages.info(request, "Your current verification application is already available.")
        return redirect("verification:application_detail", application_id=existing.public_id)

    previous_status = profile.verification_status
    application = VerificationApplication.objects.create(profile=profile)
    profile.verification_status = AdvocateProfile.VerificationStatus.DRAFT
    profile.save(update_fields=["verification_status", "updated_at"])
    VerificationReviewEvent.objects.create(
        application=application,
        actor=request.user,
        from_status=previous_status,
        to_status=VerificationApplication.Status.DRAFT,
        comment="Verification application started by advocate.",
    )
    messages.success(request, "Your verification application has been started.")
    return redirect("verification:application_detail", application_id=application.public_id)


@login_required
def application_detail(request: HttpRequest, application_id) -> HttpResponse:
    application = _owned_application(request, application_id)
    return render(
        request,
        "verification/application_detail.html",
        {
            "application": application,
            "upload_form": VerificationDocumentUploadForm(),
            "required_evidence": application.required_evidence_types(),
        },
    )


@login_required
@require_POST
def upload_document(request: HttpRequest, application_id) -> HttpResponse:
    application = _owned_application(request, application_id)
    if not application.can_edit_evidence:
        messages.error(request, "Evidence cannot be changed after submission unless more information is requested.")
        return redirect("verification:application_detail", application_id=application.public_id)

    form = VerificationDocumentUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(
            request,
            "verification/application_detail.html",
            {"application": application, "upload_form": form, "required_evidence": application.required_evidence_types()},
            status=400,
        )

    evidence_type = form.cleaned_data["evidence_type"]
    for existing in application.documents.filter(evidence_type=evidence_type).exclude(
        scan_status=VerificationDocument.ScanStatus.REPLACED
    ):
        existing.mark_replaced()

    uploaded_file = form.cleaned_data["file"]
    document = form.save(commit=False)
    document.application = application
    document.original_filename = Path(uploaded_file.name).name[:255]
    document.byte_size = uploaded_file.size
    document.save()
    queue_document_scan(document)
    messages.success(
        request,
        "Evidence uploaded and quarantined pending a security scan. It is not yet available for download.",
    )
    return redirect("verification:application_detail", application_id=application.public_id)


@login_required
@require_POST
def submit_application(request: HttpRequest, application_id) -> HttpResponse:
    application = _owned_application(request, application_id)
    try:
        application.submit(request.user)
    except ValidationError as error:
        messages.error(request, error.messages[0])
    else:
        messages.success(request, "Your verification application has been submitted for review.")
    return redirect("verification:application_detail", application_id=application.public_id)


@login_required
def download_document(request: HttpRequest, application_id, document_id) -> FileResponse:
    application = get_object_or_404(VerificationApplication, public_id=application_id)
    document = get_object_or_404(VerificationDocument, public_id=document_id, application=application)
    owns_application = request.user.is_advocate and application.profile.user_id == request.user.id
    if not (owns_application or request.user.is_staff):
        raise PermissionDenied("You do not have access to this private verification document.")
    if not document.is_available_for_download:
        raise Http404("This document is quarantined or unavailable.")
    VerificationDocumentAccessEvent.objects.create(document=document, actor=request.user)
    return FileResponse(
        document.file.open("rb"), as_attachment=True, filename=document.original_filename
    )


@staff_member_required
def review_queue(request: HttpRequest) -> HttpResponse:
    applications = VerificationApplication.objects.exclude(
        status__in=[VerificationApplication.Status.DRAFT, VerificationApplication.Status.REJECTED, VerificationApplication.Status.REVOKED]
    ).select_related("profile", "profile__user")
    return render(request, "verification/review_queue.html", {"applications": applications})


@staff_member_required
def review_application(request: HttpRequest, application_id) -> HttpResponse:
    application = get_object_or_404(
        VerificationApplication.objects.select_related("profile", "profile__user"), public_id=application_id
    )
    form = VerificationReviewForm(application, request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            application.transition(
                form.cleaned_data["status"],
                actor=request.user,
                comment=form.cleaned_data["comment"],
                expires_at=form.cleaned_data["expires_at"],
            )
        except ValidationError as error:
            form.add_error(None, error.messages[0])
        else:
            messages.success(request, "Verification decision recorded in the review history.")
            return redirect("verification:review_application", application_id=application.public_id)
    return render(
        request,
        "verification/review_application.html",
        {"application": application, "form": form},
    )
