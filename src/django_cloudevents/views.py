from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any, ClassVar

from cloudevents.http import from_http
from django.http import HttpResponse
from django.http.request import validate_host
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .conf import settings
from .processors import InvalidEventProcessorError, event_processors
from .signals import cloudevent_received

if TYPE_CHECKING:
    from django.http import HttpRequest


class WebhookView(View):
    http_method_names: ClassVar[list[str]] = ["post", "options"]

    async def post(self, request: HttpRequest) -> HttpResponse:
        cloudevent = from_http(request.headers, request.body)
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

    async def options(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        response = await super().options(request, *args, **kwargs)

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

    @method_decorator(csrf_exempt)
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return super().dispatch(request, *args, **kwargs)
