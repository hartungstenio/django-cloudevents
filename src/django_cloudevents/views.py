"""Views for handling CloudEvents webhooks in Django.

This module provides Django view classes for receiving and processing
CloudEvents from various webhook sources (e.g., GitHub, GitLab, etc.).

The main components are:

- :class:`CloudEventWebhookView`: Base class for creating custom webhook views
  that process CloudEvents. This is the recommended approach for new integrations.
"""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any

from django.http.request import validate_host
from django.views import View

from ._conf import settings

if TYPE_CHECKING:
    from collections.abc import Awaitable

    from django.http import HttpRequest, HttpResponseBase


class CloudEventWebhookView(View):
    """Base view for handling CloudEvents webhooks.

    This class provides the core logic for processing webhook requests that
    follow the CloudEvents specification. Subclasses should override the
    `post()` method to implement event-specific processing.

    The view also handles OPTIONS requests to support cross-origin webhooks
    (CORS), returning appropriate headers according to the GitHub and other
    providers webhook specification.

    Attributes:
        No class attributes.

    Example:
        ```python
        class MyEventView(CloudEventWebhookView):
            async def post(self, request):
                # Process CloudEvent
                return HttpResponse(status=202)
        ```
    """

    def options(  # type: ignore[override]
        self,
        request: HttpRequest,
        *args: Any,  # noqa: ANN401
        **kwargs: Any,  # noqa: ANN401
    ) -> HttpResponseBase | Awaitable[HttpResponseBase]:
        """Handle OPTIONS requests for webhook CORS support.

        This method overrides Django's default behavior to add support for
        webhook headers according to the GitHub webhook specification. It
        returns the `WebHook-Allowed-Origin` and `WebHook-Allowed-Rate` headers
        when appropriate.

        Args:
            request: The HttpRequest object containing the request headers.
            *args: Additional positional arguments passed by the URL.
            **kwargs: Additional keyword arguments passed by the URL.

        Returns:
            HttpResponseBase | Awaitable[HttpResponseBase]: HTTP response with
                appropriate CORS headers for webhooks.

        Note:
            This implementation supports both synchronous and asynchronous views.
        """

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
