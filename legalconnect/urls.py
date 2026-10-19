"""Root URL configuration."""

from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("account/", include("apps.accounts.urls")),
    path("verification/", include("apps.verification.urls")),
    path("", include("apps.consultations.urls")),
]
