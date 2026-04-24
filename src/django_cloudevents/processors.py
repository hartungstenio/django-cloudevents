r"""Event processors for handling CloudEvents in Django.

This module provides the infrastructure for registering and executing
processors that handle incoming CloudEvents. Processors are configured
via Django settings and can be either synchronous or asynchronous.

The module defines several base classes and protocols:

- :class:`EventProcessor`: Base class for synchronous processors
- :class:`AsyncEventProcessor`: Base class for asynchronous processors
- :class:`AcceptEventProcessor`: A simple processor that accepts all events

Configuration:
    Event processors are configured in the Django settings under
    ``CLOUDEVENT_PROCESSORS``. Each processor needs a backend class and
    a subject pattern to match event types.

Example:
    Configuration in settings.py::

        CLOUDEVENT_PROCESSORS = {
            "github_push": {
                "BACKEND": "myapp.processors.GitHubPushProcessor",
                "SUBJECT": r"github\.push",
                "OPTIONS": {},
            },
        }

    Creating a custom processor::

        from django_cloudevents.processors import AsyncEventProcessor


        class MyProcessor(AsyncEventProcessor):
            async def aprocess_event(self, cloudevent, request):
                # Process the event
                return None
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, TypedDict

from asgiref.sync import async_to_sync, sync_to_async
from django.core.exceptions import ImproperlyConfigured
from django.utils.connection import BaseConnectionHandler
from django.utils.module_loading import import_string

from ._compat import override

if TYPE_CHECKING:
    import re
    from collections.abc import Mapping

    from cloudevents.core.base import BaseCloudEvent
    from django.http import HttpRequest, HttpResponse


class EventProcessor(ABC):
    """Abstract base class for synchronous CloudEvent processors.

    This class provides a base implementation for processors that handle
    events synchronously. Subclasses must implement the ``process_event``
    method. The ``aprocess_event`` method is automatically provided using
    ``asgiref.sync.sync_to_async``.

    Attributes:
        Not applicable to abstract classes.

    Example:
        A synchronous processor::

            from django.http import HttpResponse
            from django_cloudevents.processors import EventProcessor


            class MySyncProcessor(EventProcessor):
                def process_event(self, cloudevent, request):
                    print(f"Processing: {cloudevent['type']}")
                    return HttpResponse(status=202)
    """

    @abstractmethod
    def process_event(self, cloudevent: BaseCloudEvent, request: HttpRequest) -> HttpResponse | None:
        """Process a CloudEvent synchronously.

        This method must be implemented by subclasses to handle the
        CloudEvent synchronously.

        Args:
            cloudevent: The CloudEvent object to process.
            request: The Django HTTP request object.

        Returns:
            An HttpResponse object, or None to return 202 Accepted.
        """

    async def aprocess_event(self, cloudevent: BaseCloudEvent, request: HttpRequest) -> HttpResponse | None:
        """Process a CloudEvent asynchronously (auto-generated).

        This method is automatically implemented by wrapping the
        synchronous ``process_event`` method using ``sync_to_async``.

        Args:
            cloudevent: The CloudEvent object to process.
            request: The Django HTTP request object.

        Returns:
            An HttpResponse object, or None to return 202 Accepted.
        """
        return await sync_to_async(self.process_event)(cloudevent, request)


class AsyncEventProcessor(ABC):
    """Abstract base class for asynchronous CloudEvent processors.

    This class provides a base implementation for processors that handle
    events asynchronously. Subclasses must implement the ``aprocess_event``
    method. The ``process_event`` method is automatically provided using
    ``asgiref.sync.async_to_sync``.

    Attributes:
        Not applicable to abstract classes.

    Example:
        An asynchronous processor::

            from django.http import HttpResponse
            from django_cloudevents.processors import AsyncEventProcessor


            class MyAsyncProcessor(AsyncEventProcessor):
                async def aprocess_event(self, cloudevent, request):
                    # Async processing, e.g., database queries
                    return HttpResponse(status=202)
    """

    def process_event(self, cloudevent: BaseCloudEvent, request: HttpRequest) -> HttpResponse | None:
        """Process a CloudEvent synchronously (auto-generated).

        This method is automatically implemented by wrapping the
        asynchronous ``aprocess_event`` method using ``async_to_sync``.

        Args:
            cloudevent: The CloudEvent object to process.
            request: The Django HTTP request object.

        Returns:
            An HttpResponse object, or None to return 202 Accepted.
        """
        return async_to_sync(self.aprocess_event)(cloudevent, request)

    @abstractmethod
    async def aprocess_event(self, cloudevent: BaseCloudEvent, request: HttpRequest) -> HttpResponse | None:
        """Process a CloudEvent asynchronously.

        This method must be implemented by subclasses to handle the
        CloudEvent asynchronously.

        Args:
            cloudevent: The CloudEvent object to process.
            request: The Django HTTP request object.

        Returns:
            An HttpResponse object, or None to return 202 Accepted.
        """


class AcceptEventProcessor(AsyncEventProcessor):
    """A processor that accepts all CloudEvents without processing.

    This is a no-op processor that simply accepts any CloudEvent and returns
    None (resulting in a 202 Accepted response). It can be used as a placeholder
    or for testing purposes.

    Attributes:
        Inherits from :class:`AsyncEventProcessor`.

    Example:
        Using AcceptEventProcessor in settings::

            CLOUDEVENT_PROCESSORS = {
                "default": {
                    "BACKEND": "django_cloudevents.processors.AcceptEventProcessor",
                    "SUBJECT": r".*",
                    "OPTIONS": {},
                },
            }
    """

    @override
    def process_event(self, cloudevent: BaseCloudEvent, request: HttpRequest) -> HttpResponse | None:
        """Process a CloudEvent synchronously.

        This is a no-op implementation that always returns None,
        resulting in a 202 Accepted response.

        Args:
            cloudevent: The CloudEvent object (unused).
            request: The Django HTTP request object (unused).

        Returns:
            None, indicating 202 Accepted.
        """
        return None

    @override
    async def aprocess_event(self, cloudevent: BaseCloudEvent, request: HttpRequest) -> HttpResponse | None:
        """Process a CloudEvent asynchronously.

        This is a no-op implementation that always returns None,
        resulting in a 202 Accepted response.

        Args:
            cloudevent: The CloudEvent object (unused).
            request: The Django HTTP request object (unused).

        Returns:
            None, indicating 202 Accepted.
        """
        return None


class InvalidEventProcessorError(ImproperlyConfigured):
    """Exception raised when an event processor configuration is invalid.

    This exception is raised when:
    - The backend class cannot be imported
    - The processor configuration is malformed
    - Required configuration keys are missing

    Attributes:
        Inherits from :class:`django.core.exceptions.ImproperlyConfigured`.
    """


class EventProcessorConfig(TypedDict):
    r"""Type definition for event processor configuration.

    This TypedDict defines the required and optional keys for configuring
    an event processor in the ``CLOUDEVENT_PROCESSORS`` Django setting.

    Keys:
        BACKEND: The dotted path to the processor class (required).
        SUBJECT: A regex pattern to match event types (required).
        OPTIONS: Additional keyword arguments for the processor (optional).

    Example:
        Configuration structure::

            {
                "BACKEND": "myapp.processors.MyProcessor",
                "SUBJECT": r"myapp\.event",
                "OPTIONS": {"timeout": 30},
            }
    """

    BACKEND: str
    SUBJECT: re.Pattern
    OPTIONS: Mapping[str, Any]


class EventHandler(BaseConnectionHandler):
    """Handler for managing event processor connections.

    This class extends Django's :class:`BaseConnectionHandler` to manage
    the lifecycle of event processors. It handles loading processors from
    Django settings and instantiating them on demand.

    The handler looks for configuration in the ``CLOUDEVENT_PROCESSORS``
    setting, which should be a dictionary mapping processor aliases to
    their configuration.

    Attributes:
        settings_name: The Django setting name to read configuration from.
        exception_class: The exception class to raise on errors.

    Note:
        This class uses Django's connection handler pattern, which provides
        caching and thread-safety for processor instances.
    """

    settings_name = "CLOUDEVENT_PROCESSORS"
    exception_class = InvalidEventProcessorError

    def create_connection(self, alias: str) -> EventProcessor:
        """Create and return an event processor instance for the given alias.

        This method loads the processor backend class from the configuration
        and instantiates it with the provided options.

        Args:
            alias: The key name of the processor in the CLOUDEVENT_PROCESSORS
                setting.

        Returns:
            An instance of :class:`EventProcessor`.

        Raises:
            InvalidEventProcessorError: If the backend cannot be imported or
                the configuration is invalid.
        """
        params: EventProcessorConfig = self.settings[alias]
        backend: str = params["BACKEND"]
        options: Mapping[str, Any] = params.get("OPTIONS", {})

        try:
            factory = import_string(backend)
        except ImportError as e:
            msg = f"Could not find backend {backend!r}: {e}"
            raise InvalidEventProcessorError(msg) from e
        else:
            return factory(**options)


event_processors = EventHandler()
"""Global instance of :class:`EventHandler` for accessing event processors.

This instance is used to retrieve configured event processors by their alias.
It provides a dictionary-like interface where keys are the processor aliases
defined in the ``CLOUDEVENT_PROCESSORS`` setting.

Example:
    Accessing a processor::

        from django_cloudevents.processors import event_processors

        processor = event_processors['my_processor']
        response = await processor.aprocess_event(cloudevent, request)

Note:
    Processors are loaded lazily and cached after first access.
"""
