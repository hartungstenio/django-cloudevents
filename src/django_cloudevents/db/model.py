from __future__ import annotations

from collections import ChainMap
from datetime import datetime
from typing import Any, Self

from cloudevents import abstract, conversion
from django.db import models
from django.utils import timezone

from .field_docs import FIELD_DESCRIPTIONS


class SpecVersion(models.TextChoices):
    v0_3 = "0.3", "0.3"
    v1_0 = "1.0", "1.0"


class CloudEvent(abstract.CloudEvent, models.Model):
    seq = models.BigAutoField(
        "Primary Key",
        primary_key=True,
        help_text="Database primary key",
    )
    # Context
    id = models.CharField(
        FIELD_DESCRIPTIONS["id"]["title"],
        max_length=100,
        help_text=FIELD_DESCRIPTIONS["id"]["description"],
    )
    source = models.URLField(
        FIELD_DESCRIPTIONS["source"]["title"],
        help_text=FIELD_DESCRIPTIONS["source"]["description"],
    )
    specversion = models.CharField(
        FIELD_DESCRIPTIONS["specversion"]["title"],
        max_length=3,
        choices=SpecVersion.choices,
        default=SpecVersion.v1_0,
        help_text=FIELD_DESCRIPTIONS["specversion"]["description"],
    )
    type = models.CharField(
        FIELD_DESCRIPTIONS["type"]["title"],
        max_length=100,
        help_text=FIELD_DESCRIPTIONS["type"]["description"],
    )

    datacontenttype = models.CharField(
        FIELD_DESCRIPTIONS["datacontenttype"]["title"],
        blank=True,
        max_length=100,
        help_text=FIELD_DESCRIPTIONS["datacontenttype"]["description"],
    )
    dataschema = models.URLField(
        FIELD_DESCRIPTIONS["dataschema"]["title"],
        blank=True,
        help_text=FIELD_DESCRIPTIONS["dataschema"]["description"],
    )
    subject = models.CharField(
        FIELD_DESCRIPTIONS["subject"]["title"],
        blank=True,
        max_length=100,
        help_text=FIELD_DESCRIPTIONS["subject"]["description"],
    )
    time = models.DateTimeField(
        FIELD_DESCRIPTIONS["time"]["title"],
        null=True,
        default=timezone.now,
        help_text=FIELD_DESCRIPTIONS["time"]["description"],
    )

    extensions = models.JSONField(
        "Extension Context Attributes",
        default=dict,
        help_text="Holds any additional attribute",
    )

    class Meta:
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(fields=["source", "id"]),
        ]

    @classmethod
    def create(cls, attributes: dict[str, Any], data: Any | None) -> Self:
        """Return a new unsaved instance of CloudEvent."""
        return cls(
            id=attributes["id"],
            source=attributes["source"],
            specversion=attributes["specversion"],
            type=attributes["type"],
            datacontenttype=attributes.get("datacontenttype", ""),
            dataschema=attributes.get("dataschema", ""),
            subject=attributes["subject"],
            time=datetime.fromisoformat(attributes["time"]) if "time" in attributes else None,
            extensions={name: value for name, value in attributes.items() if name not in cls._meta.get_fields()},
        )

    def _get_attributes(self):
        attributes = {
            "id": conversion.best_effort_encode_attribute_value(self.id),
            "source": conversion.best_effort_encode_attribute_value(self.source),
            "specversion": conversion.best_effort_encode_attribute_value(self.specversion),
            "type": conversion.best_effort_encode_attribute_value(self.type),
        }

        if self.datacontenttype:
            attributes["datacontenttype"] = conversion.best_effort_encode_attribute_value(self.datacontenttype)
        if self.dataschema:
            attributes["dataschema"] = conversion.best_effort_encode_attribute_value(self.dataschema)
        if self.subject:
            attributes["subject"] = conversion.best_effort_encode_attribute_value(self.subject)
        if self.time:
            attributes["time"] = conversion.best_effort_encode_attribute_value(self.time)

        return ChainMap(attributes, self.extensions)

    def get_data(self) -> Any:
        raise NotImplementedError
