from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Protocol, TypedDict

from asgiref.sync import async_to_sync, sync_to_async
from cloudevents.abstract import CloudEvent
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.utils.connection import BaseConnectionHandler
from django.utils.module_loading import import_string

if TYPE_CHECKING:
    import re
    from collections.abc import Mapping

    from cloudevents.abstract import CloudEvent
    from django.http import HttpResponse


class EventProcessor(Protocol):
    def process_event(self, cloudevent: CloudEvent) -> HttpResponse | None:
        pass

    async def aprocess_event(self, cloudevent: CloudEvent) -> HttpResponse | None:
        pass


class SyncEventProcessor(ABC):
    @abstractmethod
    def process_event(self, cloudevent: CloudEvent) -> HttpResponse | None:
        pass

    async def aprocess_event(self, cloudevent: CloudEvent) -> HttpResponse | None:
        return await sync_to_async(self.process_event)(cloudevent)


class AsyncEventProcessor(ABC):
    def process_event(self, cloudevent: CloudEvent) -> HttpResponse | None:
        return async_to_sync(self.aprocess_event)(cloudevent)

    @abstractmethod
    async def aprocess_event(self, cloudevent: CloudEvent) -> HttpResponse | None:
        pass


class AcceptEventProcessor(AsyncEventProcessor):
    def process_event(self, cloudevent: CloudEvent) -> HttpResponse | None:  # noqa: ARG002
        return None

    async def aprocess_event(self, cloudevent: CloudEvent) -> HttpResponse | None:  # noqa: ARG002
        return None


class InvalidEventProcessorError(ImproperlyConfigured):
    pass


class EventProcessorConfig(TypedDict):
    BACKEND: str
    SUBJECT: re.Pattern
    OPTIONS: Mapping[str, Any]


class EventHandler(BaseConnectionHandler):
    settings_name = "CLOUDEVENT_PROCESSORS"
    exception_class = InvalidEventProcessorError

    def create_connection(self, alias: str) -> EventProcessor:
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
