from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views


app_name = "accounts"

urlpatterns = [
    path("login/", views.LegalConnectLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/<str:role>/", views.register, name="register"),
    path("advocate/profile/", views.edit_advocate_profile, name="edit_advocate_profile"),
    path("advocate/profile/ready/", views.mark_profile_ready, name="mark_profile_ready"),
    path("advocate/profile/publish/", views.publish_profile, name="publish_profile"),
    path("advocates/<uuid:public_id>/", views.public_advocate_profile, name="public_advocate_profile"),
    path("advocates/<uuid:public_id>/photo/", views.public_advocate_photo, name="public_advocate_photo"),
]
