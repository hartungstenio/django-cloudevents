from django.urls import path

from . import views

app_name = "django_cloudevents"

urlpatterns = [
    path("", views.WebhookView.as_view(), name="webhook"),
]
