"""Django models for CloudEvents subscriptions."""

from typing import Any

from django.db import models
from django.utils.translation import gettext_lazy as _

from django_cloudevents._compat import override

from .types import FilterExpression


class Subscription(models.Model):
    """Represents a CloudEvents subscription target configuration."""

    source = models.CharField(
        _("source to which the subscription is related"),
        blank=True,
        help_text=_(
            "Indicates the source to which the subscription is related. When present on a subscribe request, all "
            "events generated due to this subscription MUST have a CloudEvents source property that matches this "
            "value. If this property is not present on a subscribe request then there are no constraints placed on the "
            "CloudEvents source property for the events generated.",
        ),
    )
    types = models.JSONField[list[str] | None](
        _("types of events the subscriber is interested in receiving"),
        null=True,
        help_text=_(
            "Indicates which types of events the subscriber is interested in receiving. When present on a subscribe "
            "request, all events generated due to this subscription MUST have a CloudEvents type property that matches "
            "one of these values.",
        ),
    )
    config = models.JSONField[dict[str, Any]](
        _("configuration of of the subscription"),
        null=True,
        help_text=_(
            "A set of key/value pairs that modify the configuration of of the subscription related to the event "
            "generation process. While this specification places no constraints on the data type of the map values. "
            "When there is a Registry Endpoint Service definition defined for the subscription manager, then the key "
            "MUST be one of the subscriptionconfig keys specified in the Registry Endpoint Service definition. The "
            "value MUST conform to the data type specified by the value in the subscriptionconfig entry for the key",
        ),
    )
    filters = models.JSONField[list[FilterExpression]](
        _("filter expressions"),
        null=True,
        help_text=_(
            "An array of filter expressions that evaluates to true or false. If any filter expression in the array "
            "evaluates to false, the event MUST NOT be sent to the sink. If all the filter expressions in the array "
            "evaluates to true, the event MUST be attempted to be delivered. Absence of a filter or empty array "
            "implies a value of true.",
        ),
    )
    sink = models.URLField(
        _("address to which events must be sent"),
        help_text=_(
            "The address to which events MUST be sent. The format of the address MUST be valid for the protocol "
            "specified in the protocol property, or one of the protocol's own transport bindings (e.g. AMQP over "
            "WebSockets).",
        ),
    )
    sinkcredential = models.JSONField[dict[str, Any]](
        _("set of settings carrying credential information"),
        null=True,
        help_text=_(
            "A set of settings carrying credential information that is enabling the entity delivering events to the "
            "subscription target to be authorized for delivery at the sink endpoint.",
        ),
    )
    protocol = models.CharField(
        _("delivery protocol"),
        help_text=_(
            "Identifier of a delivery protocol. Because of WebSocket tunneling options for AMQP, MQTT and other "
            "protocols, the URI scheme is not sufficient to identify the protocol. The protocols with existing "
            "CloudEvents bindings are identified as AMQP, MQTT3, MQTT5, HTTP, KAFKA, and NATS. An implementation MAY "
            "add support for further protocols.",
        ),
    )
    protocolsettings = models.JSONField[dict[str, Any]](
        _("settings specific to the selected delivery protocol provider"),
        null=True,
        help_text=_(
            "A set of settings specific to the selected delivery protocol provider. Options for these settings are "
            "listed in the following subsection. An subscription manager MAY offer more options.",
        ),
    )

    @override
    def __str__(self) -> str:
        return self.sink
