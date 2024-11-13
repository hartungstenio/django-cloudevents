from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any, ClassVar

from cloudevents.http import from_http
from django.conf import settings
from django.http import HttpResponse
from django.http.request import validate_host
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

if TYPE_CHECKING:
    from django.http import HttpRequest


class WebhookView(View):
    http_method_names: ClassVar[list[str]] = ["post", "options"]

    async def post(self, request: HttpRequest) -> HttpResponse:
        from_http(request.headers, request.body)
        return HttpResponse("", status=HTTPStatus.NO_CONTENT)

    async def options(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        response = await super().options(request, *args, **kwargs)

        if "WebHook-Request-Origin" in request.headers and validate_host(
            request.headers["WebHook-Request-Origin"],
            settings.WEBHOOK_ALLOWED_ORIGINS,
        ):
            any_domain = any(pattern == "*" for pattern in settings.WEBHOOK_ALLOWED_ORIGINS)
            response["WebHook-Allowed-Origin"] = "*" if any_domain else request.headers["WebHook-Request-Origin"]

            if "WebHook-Request-Rate" in request.headers:
                response["WebHook-Allowed-Rate"] = request.headers["WebHook-Request-Rate"]
        return response

    @method_decorator(csrf_exempt)
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return super().dispatch(request, *args, **kwargs)
