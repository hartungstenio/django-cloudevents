import pytest
from cloudevents.conversion import from_dict
from cloudevents.http import CloudEvent
from django.conf import settings

from django_cloudevents.processors import AcceptEventProcessor, EventHandler, InvalidEventProcessorError


class TestAcceptEventProcessor:
    def test_process_event(self, cloudevent, rf):
        given = from_dict(CloudEvent, cloudevent)
        request = rf.post("/")
        processor = AcceptEventProcessor()

        assert processor.process_event(given, request) is None

    @pytest.mark.asyncio
    async def test_aprocess_event(self, cloudevent, async_rf):
        given = from_dict(CloudEvent, cloudevent)
        request = async_rf.post("/")
        processor = AcceptEventProcessor()

        assert await processor.aprocess_event(given, request) is None


class TestEventHandler:
    def test_with_custom_settings(self):
        handler = EventHandler(
            {
                "test": {
                    "BACKEND": "django_cloudevents.processors.AcceptEventProcessor",
                }
            }
        )
        items = set(handler)

        assert items == {"test"}

    def test_with_default_settings(self):
        handler = EventHandler()
        items = set(handler)

        assert items == set(settings.CLOUDEVENT_PROCESSORS)

    def test_get_existing_item(self):
        handler = EventHandler(
            {
                "test": {
                    "BACKEND": "django_cloudevents.processors.AcceptEventProcessor",
                }
            }
        )

        got = handler["test"]

        assert isinstance(got, AcceptEventProcessor)

    def test_get_missing_item(self):
        handler = EventHandler(
            {
                "test": {
                    "BACKEND": "django_cloudevents.processors.AcceptEventProcessor",
                }
            }
        )

        with pytest.raises(InvalidEventProcessorError):
            handler["missing"]
