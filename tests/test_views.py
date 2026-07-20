from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from django.test import RequestFactory, override_settings

from django_cloudevents.views import CloudEventWebhookView

if TYPE_CHECKING:
    from django.http import HttpResponseBase

pytestmark = pytest.mark.django_db


class TestCloudEventWebhookView:
    def test_options_without_request_origin(self, rf: RequestFactory) -> None:
        request = rf.options("/")
        view = CloudEventWebhookView()

        response: HttpResponseBase = view.dispatch(request)

        assert response.status_code == HTTPStatus.OK
        assert "WebHook-Allowed-Origin" not in response.headers
        assert "WebHook-Allowed-Rate" not in response.headers

    @override_settings(WEBHOOK_ALLOWED_ORIGINS=["*"], WEBHOOK_ALLOWED_RATE=None)
    def test_options_with_every_allowed_origin(self, rf: RequestFactory) -> None:
        request = rf.options("/", headers={"WebHook-Request-Origin": "eventemitter.example.com"})
        view = CloudEventWebhookView()

        response: HttpResponseBase = view.dispatch(request)

        assert response.status_code == HTTPStatus.OK
        assert response.headers["WebHook-Allowed-Origin"] == "*"
        assert "WebHook-Allowed-Rate" not in response.headers

    @override_settings(WEBHOOK_ALLOWED_ORIGINS=["eventemitter.example.com"], WEBHOOK_ALLOWED_RATE=None)
    def test_options_with_allowed_origin(self, rf: RequestFactory) -> None:
        request = rf.options("/", headers={"WebHook-Request-Origin": "eventemitter.example.com"})
        view = CloudEventWebhookView()

        response: HttpResponseBase = view.dispatch(request)

        assert response.status_code == HTTPStatus.OK
        assert response.headers["WebHook-Allowed-Origin"] == "eventemitter.example.com"
        assert "WebHook-Allowed-Rate" not in response.headers

    @override_settings(WEBHOOK_ALLOWED_ORIGINS=["eventemitter.example.com"], WEBHOOK_ALLOWED_RATE=None)
    def test_options_with_allowed_origin_and_rate(self, rf: RequestFactory) -> None:
        request = rf.options(
            "/",
            headers={
                "WebHook-Request-Origin": "eventemitter.example.com",
                "WebHook-Request-Rate": "100",
            },
        )
        view = CloudEventWebhookView()

        response: HttpResponseBase = view.dispatch(request)

        assert response.status_code == HTTPStatus.OK
        assert response.headers["WebHook-Allowed-Origin"] == "eventemitter.example.com"
        assert response.headers["WebHook-Allowed-Rate"] == "100"

    @override_settings(
        WEBHOOK_ALLOWED_ORIGINS=["eventemitter.example.com"],
        WEBHOOK_ALLOWED_RATE=50,
    )
    def test_options_with_allowed_origin_and_custom_rate(self, rf: RequestFactory) -> None:
        request = rf.options(
            "/",
            headers={
                "WebHook-Request-Origin": "eventemitter.example.com",
                "WebHook-Request-Rate": "100",
            },
        )
        view = CloudEventWebhookView()

        response: HttpResponseBase = view.dispatch(request)

        assert response.status_code == HTTPStatus.OK
        assert response.headers["WebHook-Allowed-Origin"] == "eventemitter.example.com"
        assert response.headers["WebHook-Allowed-Rate"] == "50"

    @override_settings(
        WEBHOOK_ALLOWED_ORIGINS=["eventemitter.example.com"],
        WEBHOOK_ALLOWED_RATE="*",
    )
    def test_options_with_allowed_origin_and_unlimited_rate(self, rf: RequestFactory) -> None:
        request = rf.options(
            "/",
            headers={
                "WebHook-Request-Origin": "eventemitter.example.com",
                "WebHook-Request-Rate": "100",
            },
        )
        view = CloudEventWebhookView()

        response: HttpResponseBase = view.dispatch(request)

        assert response.status_code == HTTPStatus.OK
        assert response.headers["WebHook-Allowed-Origin"] == "eventemitter.example.com"
        assert response.headers["WebHook-Allowed-Rate"] == "*"

    @override_settings(
        WEBHOOK_ALLOWED_ORIGINS=["eventemitter.example.com"],
        WEBHOOK_ALLOWED_RATE="*",
    )
    def test_options_with_denied_origin(self, rf: RequestFactory) -> None:
        request = rf.options(
            "/",
            headers={
                "WebHook-Request-Origin": "denied.example.com",
                "WebHook-Request-Rate": "100",
            },
        )
        view = CloudEventWebhookView()

        response: HttpResponseBase = view.dispatch(request)

        assert response.status_code == HTTPStatus.OK
        assert "WebHook-Allowed-Origin" not in response.headers
        assert "WebHook-Allowed-Rate" not in response.headers
