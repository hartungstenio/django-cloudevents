from http import HTTPStatus
from unittest import mock

import pytest
from django.http import HttpResponse
from django.test import Client, override_settings
from django.urls import reverse

from django_cloudevents.signals import cloudevent_received

pytestmark = pytest.mark.django_db


class TestWebhookView:
    def test_options_without_request_origin(self, client: Client):
        response: HttpResponse = client.options(reverse("django_cloudevents:webhook"))

        assert response.status_code == HTTPStatus.OK
        assert "WebHook-Allowed-Origin" not in response.headers
        assert "WebHook-Allowed-Rate" not in response.headers

    @override_settings(CLOUDEVENTS={"WEBHOOK_ALLOWED_ORIGINS": ["*"]})
    def test_options_with_every_allowed_origin(self, client: Client):
        response: HttpResponse = client.options(
            reverse("django_cloudevents:webhook"), headers={"WebHook-Request-Origin": "eventemitter.example.com"}
        )

        assert response.status_code == HTTPStatus.OK
        assert response.headers["WebHook-Allowed-Origin"] == "*"
        assert "WebHook-Allowed-Rate" not in response.headers

    @override_settings(CLOUDEVENTS={"WEBHOOK_ALLOWED_ORIGINS": ["eventemitter.example.com"]})
    def test_options_with_allowed_origin(self, client: Client):
        response: HttpResponse = client.options(
            reverse("django_cloudevents:webhook"), headers={"WebHook-Request-Origin": "eventemitter.example.com"}
        )

        assert response.status_code == HTTPStatus.OK
        assert response.headers["WebHook-Allowed-Origin"] == "eventemitter.example.com"
        assert "WebHook-Allowed-Rate" not in response.headers

    @override_settings(CLOUDEVENTS={"WEBHOOK_ALLOWED_ORIGINS": ["eventemitter.example.com"]})
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

    @override_settings(
        CLOUDEVENTS={
            "WEBHOOK_ALLOWED_ORIGINS": ["eventemitter.example.com"],
            "WEBHOOK_ALLOWED_RATE": 50,
        }
    )
    def test_options_with_allowed_origin_and_custom_rate(self, client: Client):
        response: HttpResponse = client.options(
            reverse("django_cloudevents:webhook"),
            headers={
                "WebHook-Request-Origin": "eventemitter.example.com",
                "WebHook-Request-Rate": "100",
            },
        )

        assert response.status_code == HTTPStatus.OK
        assert response.headers["WebHook-Allowed-Origin"] == "eventemitter.example.com"
        assert response.headers["WebHook-Allowed-Rate"] == "50"

    @override_settings(
        CLOUDEVENTS={
            "WEBHOOK_ALLOWED_ORIGINS": ["eventemitter.example.com"],
            "WEBHOOK_ALLOWED_RATE": "*",
        }
    )
    def test_options_with_allowed_origin_and_unlimited_rate(self, client: Client):
        response: HttpResponse = client.options(
            reverse("django_cloudevents:webhook"),
            headers={
                "WebHook-Request-Origin": "eventemitter.example.com",
                "WebHook-Request-Rate": "100",
            },
        )

        assert response.status_code == HTTPStatus.OK
        assert response.headers["WebHook-Allowed-Origin"] == "eventemitter.example.com"
        assert response.headers["WebHook-Allowed-Rate"] == "*"

    @override_settings(
        CLOUDEVENTS={
            "WEBHOOK_ALLOWED_ORIGINS": ["eventemitter.example.com"],
            "WEBHOOK_ALLOWED_RATE": "*",
        }
    )
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

    def test_post_no_receivers(self, cloudevent, client: Client):
        response: HttpResponse = client.post(
            reverse("django_cloudevents:webhook"), data=cloudevent, content_type="application/json"
        )

        assert response.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE

    def test_post_calls_signals(self, cloudevent, client: Client):
        mock_signal = mock.Mock()

        cloudevent_received.connect(mock_signal)
        try:
            response: HttpResponse = client.post(
                reverse("django_cloudevents:webhook"), data=cloudevent, content_type="application/json"
            )

            assert response.status_code == HTTPStatus.ACCEPTED
            mock_signal.assert_called_once()
        finally:
            cloudevent_received.disconnect(mock_signal)

    def test_post_custom_response(self, cloudevent, client: Client):
        mock_signal = mock.Mock()
        expected = HttpResponse("", status=HTTPStatus.OK)
        mock_signal.return_value = expected

        cloudevent_received.connect(mock_signal)
        try:
            response: HttpResponse = client.post(
                reverse("django_cloudevents:webhook"), data=cloudevent, content_type="application/json"
            )

            assert response == expected
            mock_signal.assert_called_once()
        finally:
            cloudevent_received.disconnect(mock_signal)
