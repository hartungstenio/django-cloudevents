from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from django.conf import settings as django_settings
from django.core.signals import setting_changed

if TYPE_CHECKING:
    from collections.abc import Sequence


class Settings:
    @property
    def webhook_allowed_origins(self) -> Sequence[str]:
        return getattr(django_settings, "WEBHOOK_ALLOWED_ORIGINS", ["*"])

    @property
    def webhook_allow_all_origins(self) -> bool:
        return self.webhook_allowed_origins == ["*"]

    @property
    def webhook_allowed_rate(self) -> int | Literal["*"] | None:
        return getattr(django_settings, "WEBHOOK_ALLOWED_RATE", None)


settings = Settings()


def reload_settings(*args, **kwargs):  # noqa: ARG001
    setting = kwargs["setting"]
    if setting == "CLOUDEVENTS":
        settings.settings = getattr(django_settings, "CLOUDEVENTS", {})


setting_changed.connect(reload_settings)
