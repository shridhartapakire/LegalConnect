from django.contrib import admin

from .models import VerificationApplication, VerificationDocument, VerificationDocumentAccessEvent, VerificationEvidenceType, VerificationReviewEvent


@admin.register(VerificationEvidenceType)
class VerificationEvidenceTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_required", "is_active", "display_order")
    list_editable = ("is_required", "is_active", "display_order")


class VerificationDocumentInline(admin.TabularInline):
    model = VerificationDocument
    extra = 0
    readonly_fields = ("public_id", "original_filename", "byte_size", "scan_status", "uploaded_at")
    fields = readonly_fields


class VerificationReviewEventInline(admin.TabularInline):
    model = VerificationReviewEvent
    extra = 0
    readonly_fields = ("actor", "from_status", "to_status", "comment", "created_at")
    can_delete = False


@admin.register(VerificationApplication)
class VerificationApplicationAdmin(admin.ModelAdmin):
    list_display = ("profile", "status", "submitted_at", "expires_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("profile__user__email", "profile__professional_name")
    readonly_fields = ("profile", "public_id", "status", "submitted_at", "reviewed_at", "expires_at", "policy_version", "created_at", "updated_at")
    inlines = (VerificationDocumentInline, VerificationReviewEventInline)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(VerificationDocument)
class VerificationDocumentAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "application", "evidence_type", "scan_status", "uploaded_at")
    list_filter = ("scan_status", "evidence_type")
    readonly_fields = (
        "public_id",
        "application",
        "evidence_type",
        "original_filename",
        "file",
        "byte_size",
        "scan_status",
        "uploaded_at",
        "replaced_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(VerificationReviewEvent)
class VerificationReviewEventAdmin(admin.ModelAdmin):
    list_display = ("application", "from_status", "to_status", "actor", "created_at")
    readonly_fields = ("application", "actor", "from_status", "to_status", "comment", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(VerificationDocumentAccessEvent)
class VerificationDocumentAccessEventAdmin(admin.ModelAdmin):
    list_display = ("document", "actor", "action", "created_at")
    readonly_fields = ("document", "actor", "action", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
