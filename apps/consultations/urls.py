from django.urls import path
from . import views

app_name = "consultations"
urlpatterns = [
    path("advocates/", views.directory, name="directory"),
    path("advocates/<uuid:public_id>/request/", views.create_request, name="create_request"),
    path("requests/", views.client_requests, name="client_requests"),
    path("requests/<uuid:request_id>/", views.client_request_detail, name="client_request_detail"),
    path("requests/<uuid:request_id>/withdraw/", views.withdraw_request, name="withdraw_request"),
    path("advocate/requests/", views.advocate_requests, name="advocate_requests"),
    path("advocate/requests/<uuid:request_id>/", views.advocate_request_detail, name="advocate_request_detail"),
    path("advocate/requests/<uuid:request_id>/start-review/", views.start_review, name="start_review"),
    path("advocate/requests/<uuid:request_id>/accept/", views.accept_request, name="accept_request"),
    path("advocate/requests/<uuid:request_id>/decline/", views.decline_request, name="decline_request"),
]
