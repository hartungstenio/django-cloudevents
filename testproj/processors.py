import sys
from http import HTTPStatus

from cloudevents.core.base import BaseCloudEvent
from cloudevents.core.bindings.http import to_structured_event
from django.http import HttpRequest, HttpResponse

from django_cloudevents.processors import EventProcessor

if sys.version_info < (3, 12):
    from typing_extensions import override
else:
    from typing import override


class EchoEventProcessor(EventProcessor):
    def __init__(self, *, status_code: HTTPStatus = HTTPStatus.ACCEPTED) -> None:
        self.status_code = status_code

    @override
    def process_event(self, cloudevent: BaseCloudEvent, request: HttpRequest) -> HttpResponse:
        message = to_structured_event(cloudevent)
        return HttpResponse(message.body, status=self.status_code, headers=message.headers)
