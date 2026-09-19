from django.urls import path

from . import views


app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("health/", views.health, name="health"),
    path("dashboard/", views.dashboard_redirect, name="dashboard_redirect"),
    path("client/dashboard/", views.client_dashboard, name="client_dashboard"),
    path("advocate/dashboard/", views.advocate_dashboard, name="advocate_dashboard"),
]
