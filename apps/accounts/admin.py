from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AdvocateProfile, ClientProfile, Language, Locality, PracticeArea, User


@admin.register(User)
class LegalConnectUserAdmin(UserAdmin):
    ordering = ("email",)
    list_display = ("email", "primary_role", "is_staff", "is_active")
    list_filter = ("primary_role", "is_staff", "is_active")
    search_fields = ("email",)
    fieldsets = (
        (None, {"fields": ("email", "password")} ),
        ("Role and status", {"fields": ("primary_role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")} ),
        ("Important dates", {"fields": ("last_login", "date_joined")} ),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "primary_role", "password1", "password2")} ),
    )
    readonly_fields = ("date_joined", "last_login")


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "locality", "created_at")
    search_fields = ("user__email", "display_name", "locality")


@admin.register(AdvocateProfile)
class AdvocateProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "professional_name", "publication_status", "verification_status", "created_at")
    list_filter = ("publication_status", "verification_status")
    search_fields = ("user__email", "professional_name")
    filter_horizontal = ("practice_areas", "languages", "service_areas")
    readonly_fields = ("verification_status", "publication_status", "public_id")


@admin.register(PracticeArea)
class PracticeAreaAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "display_order")
    list_editable = ("is_active", "display_order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active", "display_order")
    list_editable = ("is_active", "display_order")


@admin.register(Locality)
class LocalityAdmin(admin.ModelAdmin):
    list_display = ("name", "district_or_region", "is_active", "display_order")
    list_editable = ("is_active", "display_order")
