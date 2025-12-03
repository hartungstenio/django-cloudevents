from __future__ import annotations

import inspect
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from cloudevents.http import from_http
from django.http import HttpResponse, HttpResponseBase
from django.http.request import validate_host
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .conf import settings
from .processors import InvalidEventProcessorError, event_processors
from .signals import cloudevent_received

if TYPE_CHECKING:
    from collections.abc import Awaitable

    from django.http import HttpRequest


class CloudEventWebhookView(View):
    def options(  # type: ignore[override]
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase | Awaitable[HttpResponseBase]:
        def _cloudevent_response_meta(response: HttpResponseBase) -> HttpResponseBase:
            if "WebHook-Request-Origin" in request.headers and validate_host(
                request.headers["WebHook-Request-Origin"],
                settings.webhook_allowed_origins,
            ):
                response["WebHook-Allowed-Origin"] = (
                    "*" if settings.webhook_allow_all_origins else request.headers["WebHook-Request-Origin"]
                )

                if settings.webhook_allowed_rate:
                    response["WebHook-Allowed-Rate"] = str(settings.webhook_allowed_rate)
                elif "WebHook-Request-Rate" in request.headers:
                    response["WebHook-Allowed-Rate"] = request.headers["WebHook-Request-Rate"]

            return response

        response: HttpResponseBase | Awaitable[HttpResponseBase] = super().options(request, *args, **kwargs)

        if inspect.isawaitable(response):

            async def func() -> HttpResponseBase:
                return _cloudevent_response_meta(await response)

            return func()

        return _cloudevent_response_meta(response)


@method_decorator(csrf_exempt, name="dispatch")
class WebhookView(CloudEventWebhookView):
    http_method_names: list[str] = ["post", "options"]  # noqa: RUF012

    async def post(self, request: HttpRequest) -> HttpResponse:
        cloudevent = from_http(dict(request.headers.items()), request.body)
        await cloudevent_received.asend(None, cloudevent=cloudevent)

        try:
            event_processor = event_processors[cloudevent["type"]]
        except InvalidEventProcessorError:
            return HttpResponse(status=HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
        else:
            response = await event_processor.aprocess_event(cloudevent, request)
            if not response:
                return HttpResponse(status=HTTPStatus.ACCEPTED)
            return response
