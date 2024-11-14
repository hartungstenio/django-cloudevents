from django.urls import include, path

urlpatterns = [
    path("", include("django_cloudevents.urls", namespace="django_cloudevents")),
]
