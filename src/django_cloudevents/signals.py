"""Signals for CloudEvents integration in Django.

This module provides Django signals that are emitted during the lifecycle
of CloudEvent processing in the library. These signals allow other parts of
the application to react to incoming CloudEvents without tightly coupling
to the webhook processing logic.

Signals:
    cloudevent_received: Emitted when a CloudEvent is received via webhook.

Example:
    Connecting a handler to the cloudevent_received signal::

        from django.dispatch import receiver
        from django_cloudevents.signals import cloudevent_received


        @receiver(cloudevent_received)
        def handle_cloudevent(sender, cloudevent, **kwargs):
            # Process the CloudEvent
            print(f"Received event: {cloudevent['type']}")
"""

from ._compat import Signal

cloudevent_received = Signal()
"""Signal emitted when a CloudEvent is received via webhook.

This signal is sent after a CloudEvent has been parsed from an incoming
HTTP request but before it is processed by any event processor. It allows
listeners to perform additional processing, logging, or validation on the
event.

Signal Arguments:
    cloudevent: The CloudEvent object parsed from the request. This is an
        instance of a CloudEvent from the `cloudevents` SDK.

Example:
    Handling the signal::

        from django.dispatch import receiver
        from django_cloudevents.signals import cloudevent_received

        @receiver(cloudevent_received)
        def log_event(sender, cloudevent, **kwargs):
            logger.info(f"Event type: {cloudevent['type']}, "
                       f"source: {cloudevent['source']}")
"""
