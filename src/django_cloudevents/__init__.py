"""Django integration for CloudEvents webhooks.

This package provides Django integration for receiving and processing
CloudEvents from various webhook sources (e.g., GitHub, GitLab, etc.).

The main features include:

- Webhook views for receiving CloudEvent requests
- Event processor infrastructure for handling different event types
- Django signals for reacting to incoming events
- Support for both synchronous and asynchronous processors

Quick start::

    from django.urls import path
    from django_cloudevents.views import CloudEventWebhookView


    class MyWebhookView(CloudEventWebhookView):
        async def post(self, request):
            # Process the CloudEvent
            return HttpResponse(status=202)


    urlpatterns = [
        path("webhook/", MyWebhookView.as_view()),
    ]

For more information about CloudEvents, see:
https://cloudevents.io/
"""

import django_stubs_ext

django_stubs_ext.monkeypatch()

del django_stubs_ext
