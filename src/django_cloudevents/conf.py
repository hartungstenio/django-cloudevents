from collections.abc import Sequence

from django.conf import settings as django_settings
from django.core.signals import setting_changed


class Settings:
    def __init__(self):
        self.settings = getattr(django_settings, "CLOUDEVENTS", {})

    @property
    def webhook_allowed_origins(self) -> Sequence[str]:
        return self.settings.get("WEBHOOK_ALLOWED_ORIGINS", ["*"])

    @property
    def webhook_allow_all_origins(self) -> bool:
        return self.webhook_allowed_origins == ["*"]


settings = Settings()


def reload_settings(*args, **kwargs):  # noqa: ARG001
    setting = kwargs["setting"]
    if setting == "CLOUDEVENTS":
        settings.settings = getattr(django_settings, "CLOUDEVENTS", {})


setting_changed.connect(reload_settings)
