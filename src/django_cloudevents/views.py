"""Views for handling CloudEvents webhooks in Django.

This module provides Django view classes for receiving and processing
CloudEvents from various webhook sources (e.g., GitHub, GitLab, etc.).

The main components are:

- :class:`CloudEventWebhookView`: Base class for creating custom webhook views
  that process CloudEvents. This is the recommended approach for new integrations.

- :class:`WebhookView`: Legacy webhook view that automatically processes events
  using registered event processors. This class is deprecated and should not
  be used for new code.
"""

from __future__ import annotations

import inspect
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from cloudevents.core.bindings.http import HTTPMessage, from_http_event
from django.http import HttpResponse, HttpResponseBase
from django.http.request import validate_host
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from ._compat import deprecated
from ._conf import settings
from .processors import InvalidEventProcessorError, event_processors
from .signals import cloudevent_received

if TYPE_CHECKING:
    from collections.abc import Awaitable

    from django.http import HttpRequest


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


@deprecated("Use a view custom view inheriting from CloudEventWebhookView")
@method_decorator(csrf_exempt, name="dispatch")
class WebhookView(CloudEventWebhookView):
    """Webhook view for receiving CloudEvents (deprecated).

    .. deprecated::
        Use a custom view that inherits from :class:`CloudEventWebhookView`.

    This class was the default view for processing CloudEvent webhooks but
    is now deprecated. It is recommended to create a custom view that inherits
    from :class:`CloudEventWebhookView` and overrides the `post()` method as
    needed.

    Attributes:
        http_method_names: List of allowed HTTP methods. Only 'post' and
            'options' are accepted.

    Example:
        ```python
        # Old (deprecated):
        urlpatterns = [
            path("webhook/", WebhookView.as_view()),
        ]


        # New (recommended):
        class MyWebhookView(CloudEventWebhookView):
            async def post(self, request):
                return HttpResponse(status=202)


        urlpatterns = [
            path("webhook/", MyWebhookView.as_view()),
        ]
        ```
    """

    http_method_names: list[str] = ["post", "options"]  # noqa: RUF012

    async def post(self, request: HttpRequest) -> HttpResponse:
        """Process POST requests containing CloudEvents.

        This method receives a POST request containing a CloudEvent in the
        message body, processes the event using the appropriate processor,
        and returns an HTTP response.

        The processing flow is:
        1. Parse the CloudEvent from request headers and body
        2. Send the :attr:`cloudevent_received` signal to notify listeners
        3. Find the appropriate event processor by event type
        4. Execute the event processor

        Args:
            request: The HttpRequest object containing the headers and body
                of the request with the CloudEvent.

        Returns:
            HttpResponse: HTTP response indicating the processing result.
                - 202 (Accepted): Event processed successfully with no specific
                  response from the processor
                - Processor response: If the processor returns a response
                - 415 (Unsupported Media Type): If no processor is found
                  for the event type

        Raises:
            Any unhandled exception will be propagated to Django's error
            handling middleware.
        """
        message = HTTPMessage(dict(request.headers), request.body)
        cloudevent = from_http_event(message)
        await cloudevent_received.asend(None, cloudevent=cloudevent)

        try:
            event_processor = event_processors[cloudevent.get_type()]
        except InvalidEventProcessorError:
            return HttpResponse(status=HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
        else:
            response = await event_processor.aprocess_event(cloudevent, request)
            if not response:
                return HttpResponse(status=HTTPStatus.ACCEPTED)
            return response
