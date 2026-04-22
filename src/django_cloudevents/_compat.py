import sys
from typing import Any

import django
from asgiref.sync import sync_to_async
from django.dispatch import Signal as _DjangoSignal

if sys.version_info < (3, 12):
    from typing_extensions import override
else:
    from typing import override

if sys.version_info < (3, 13):
    from typing_extensions import deprecated
else:
    from warnings import deprecated

if django.VERSION >= (5, 0):
    Signal = _DjangoSignal
else:

    class Signal(_DjangoSignal):  # type: ignore[no-redef]
        async def asend(self, *args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            return await sync_to_async(self.send)(*args, **kwargs)


__all__ = [
    "Signal",
    "deprecated",
    "override",
]
