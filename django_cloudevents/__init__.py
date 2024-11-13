from django.urls import path

from . import views

urlpatterns = [
    path("", views.WebhookView.as_view(), name="webhook"),
]
