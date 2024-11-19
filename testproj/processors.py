import sys
from http import HTTPStatus

from cloudevents.abstract import CloudEvent
from cloudevents.conversion import to_structured
from django.http import HttpRequest, HttpResponse

from django_cloudevents.processors import SyncEventProcessor

if sys.version_info < (3, 12):
    from typing_extensions import override
else:
    from typing import override


class EchoEventProcessor(SyncEventProcessor):
    def __init__(self, *, status_code: HTTPStatus = HTTPStatus.ACCEPTED):
        self.status_code = status_code

    @override
    def process_event(self, cloudevent: CloudEvent, request: HttpRequest) -> HttpResponse:
        headers, data = to_structured(cloudevent)
        return HttpResponse(data, status=self.status_code, headers=headers)
