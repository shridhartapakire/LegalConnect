from django.urls import path

from . import views


app_name = "verification"

urlpatterns = [
    path("start/", views.start_application, name="start_application"),
    path("<uuid:application_id>/", views.application_detail, name="application_detail"),
    path("<uuid:application_id>/upload/", views.upload_document, name="upload_document"),
    path("<uuid:application_id>/submit/", views.submit_application, name="submit_application"),
    path(
        "<uuid:application_id>/documents/<uuid:document_id>/download/",
        views.download_document,
        name="download_document",
    ),
    path("management/", views.review_queue, name="review_queue"),
    path("management/<uuid:application_id>/", views.review_application, name="review_application"),
]
