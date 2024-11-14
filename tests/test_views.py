from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from django.test import Client, override_settings
from django.urls import reverse

if TYPE_CHECKING:
    from django.http import HttpResponse

pytestmark = pytest.mark.django_db


class TestWebhookView:
    def test_options_without_request_origin(self, client: Client):
        response: HttpResponse = client.options(reverse("django_cloudevents:webhook"))

        assert response.status_code == HTTPStatus.OK
        assert "WebHook-Allowed-Origin" not in response.headers
        assert "WebHook-Allowed-Rate" not in response.headers

    @override_settings(WEBHOOK_ALLOWED_ORIGINS=["*"])
    def test_options_with_every_allowed_origin(self, client: Client):
        response: HttpResponse = client.options(
            reverse("django_cloudevents:webhook"), headers={"WebHook-Request-Origin": "eventemitter.example.com"}
        )

        assert response.status_code == HTTPStatus.OK
        assert response.headers["WebHook-Allowed-Origin"] == "*"
        assert "WebHook-Allowed-Rate" not in response.headers

    @override_settings(WEBHOOK_ALLOWED_ORIGINS=["eventemitter.example.com"])
    def test_options_with_allowed_origin(self, client: Client):
        response: HttpResponse = client.options(
            reverse("django_cloudevents:webhook"), headers={"WebHook-Request-Origin": "eventemitter.example.com"}
        )

        assert response.status_code == HTTPStatus.OK
        assert response.headers["WebHook-Allowed-Origin"] == "eventemitter.example.com"
        assert "WebHook-Allowed-Rate" not in response.headers

    @override_settings(WEBHOOK_ALLOWED_ORIGINS=["eventemitter.example.com"])
    def test_options_with_allowed_origin_and_rate(self, client: Client):
        response: HttpResponse = client.options(
            reverse("django_cloudevents:webhook"),
            headers={
                "WebHook-Request-Origin": "eventemitter.example.com",
                "WebHook-Request-Rate": "100",
            },
        )

        assert response.status_code == HTTPStatus.OK
        assert response.headers["WebHook-Allowed-Origin"] == "eventemitter.example.com"
        assert response.headers["WebHook-Allowed-Rate"] == "100"

    @override_settings(WEBHOOK_ALLOWED_ORIGINS=["eventemitter.example.com"])
    def test_options_with_denied_origin(self, client: Client):
        response: HttpResponse = client.options(
            reverse("django_cloudevents:webhook"),
            headers={
                "WebHook-Request-Origin": "denied.example.com",
                "WebHook-Request-Rate": "100",
            },
        )

        assert response.status_code == HTTPStatus.OK
        assert "WebHook-Allowed-Origin" not in response.headers
        assert "WebHook-Allowed-Rate" not in response.headers
