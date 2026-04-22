from collections.abc import Mapping
from typing import Any

import pytest
from django.utils import timezone


@pytest.fixture
def cloudevent() -> Mapping[str, Any]:
    return {
        "specversion": "1.0",
        "type": "com.github.pull_request.opened",
        "source": "https://github.com/cloudevents/spec/pull",
        "subject": "123",
        "id": "A234-1234-1234",
        "time": timezone.now(),
        "comexampleextension1": "value",
        "comexampleothervalue": 5,
        "datacontenttype": "text/xml",
        "data": '<much wow="xml"/>',
    }
