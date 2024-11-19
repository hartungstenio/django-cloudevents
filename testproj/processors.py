from http import HTTPStatus

from cloudevents.abstract import CloudEvent
from cloudevents.conversion import to_structured
from django.http import HttpRequest, HttpResponse

from django_cloudevents.processors import SyncEventProcessor


class EchoEventProcessor(SyncEventProcessor):
    def __init__(self, *, status_code: HTTPStatus = HTTPStatus.ACCEPTED):
        self.status_code = status_code

    def process_event(self, cloudevent: CloudEvent, request: HttpRequest) -> HttpResponse:  # noqa: ARG002
        headers, data = to_structured(cloudevent)
        return HttpResponse(data, status=self.status_code, headers=headers)
