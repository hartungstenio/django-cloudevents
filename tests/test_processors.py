from collections.abc import Mapping
from typing import Any

import pytest
from cloudevents.core.v1.event import CloudEvent
from django.conf import settings
from django.test import AsyncRequestFactory, RequestFactory

from django_cloudevents.processors import AcceptEventProcessor, EventHandler, InvalidEventProcessorError


class TestAcceptEventProcessor:
    def test_process_event(self, cloudevent: Mapping[str, Any], rf: RequestFactory) -> None:
        data = cloudevent.pop("data")
        given = CloudEvent(attributes=cloudevent, data=data)
        request = rf.post("/")
        processor = AcceptEventProcessor()

        assert processor.process_event(given, request) is None

    @pytest.mark.asyncio
    async def test_aprocess_event(self, cloudevent: Mapping[str, Any], async_rf: AsyncRequestFactory) -> None:
        data = cloudevent.pop("data")
        given = CloudEvent(attributes=cloudevent, data=data)
        request = async_rf.post("/")
        processor = AcceptEventProcessor()

        assert await processor.aprocess_event(given, request) is None


class TestEventHandler:
    def test_with_custom_settings(self) -> None:
        handler = EventHandler(
            {
                "test": {
                    "BACKEND": "django_cloudevents.processors.AcceptEventProcessor",
                },
            },
        )
        items = set(handler)

        assert items == {"test"}

    def test_with_default_settings(self) -> None:
        handler = EventHandler()
        items = set(handler)

        assert items == set(settings.CLOUDEVENT_PROCESSORS)

    def test_get_existing_item(self) -> None:
        handler = EventHandler(
            {
                "test": {
                    "BACKEND": "django_cloudevents.processors.AcceptEventProcessor",
                },
            },
        )

        got = handler["test"]

        assert isinstance(got, AcceptEventProcessor)

    def test_get_missing_item(self) -> None:
        handler = EventHandler(
            {
                "test": {
                    "BACKEND": "django_cloudevents.processors.AcceptEventProcessor",
                },
            },
        )

        with pytest.raises(InvalidEventProcessorError):
            handler["missing"]
