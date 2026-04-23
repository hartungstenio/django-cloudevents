"""Django Channels integration for CloudEvents.

This module provides WebSocket consumers that handle CloudEvents over
Django Channels connections. It supports subprotocol negotiation for
encoding/decoding CloudEvents in JSON format.
"""

from collections.abc import Sequence
from typing import ClassVar, Protocol, TypedDict

from asgiref.sync import async_to_sync
from asgiref.typing import WebSocketConnectEvent
from channels.exceptions import AcceptConnection, DenyConnection, InvalidChannelLayerError
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from cloudevents.core.base import BaseCloudEvent
from cloudevents.core.formats.base import Format
from cloudevents.core.formats.json import JSONFormat

from django_cloudevents._compat import NotRequired, Unpack, override

SEC_WS_PROTOCOL = b"sec-websocket-protocol"


class ChannelEncoding(TypedDict):
    """TypedDict representing the encoding format for channel data.

    Attributes:
        text_data: Optional string data for text-based encoding.
        bytes_data: Optional bytes data for binary encoding.
    """

    text_data: NotRequired[str | None]
    bytes_data: NotRequired[bytes | None]


class Subprotocol(Format, Protocol):
    """Protocol defining the interface for CloudEvent subprotocols.

    This protocol extends the Format class and defines methods for handling
    subprotocol negotiation, encoding, and decoding of CloudEvents in channels.

    Attributes:
        subprotocol: The subprotocol string identifier.
    """

    subprotocol: ClassVar[str]

    def accepts(self, subprotocol: str) -> bool:
        """Check if this subprotocol accepts the given subprotocol string.

        Args:
            subprotocol: The subprotocol string to check.

        Returns:
            True if accepted, False otherwise.
        """

    def encode(self, cloudevent: BaseCloudEvent) -> ChannelEncoding:
        """Encode a CloudEvent into channel data format.

        Args:
            cloudevent: The CloudEvent to encode.

        Returns:
            A ChannelEncoding dict with the encoded data.
        """

    def decode(self, **kwargs: Unpack[ChannelEncoding]) -> BaseCloudEvent:
        """Decode channel data into a CloudEvent.

        Args:
            **kwargs: Keyword arguments from ChannelEncoding.

        Returns:
            The decoded CloudEvent.
        """


class JSONSubprotocol(Subprotocol, JSONFormat):
    """JSON-based subprotocol for CloudEvents.

    Implements the Subprotocol interface using JSON format for encoding
    and decoding CloudEvents over WebSocket channels.
    """

    subprotocol = "cloudevents.json"

    def accepts(self, subprotocol: str) -> bool:
        """Check if this subprotocol accepts 'cloudevents.json'.

        Args:
            subprotocol: The subprotocol string.

        Returns:
            True if 'cloudevents.json', False otherwise.
        """
        return subprotocol == self.subprotocol

    def encode(self, cloudevent: BaseCloudEvent) -> ChannelEncoding:
        """Encode a CloudEvent to JSON text data.

        Args:
            cloudevent: The CloudEvent to encode.

        Returns:
            ChannelEncoding with text_data containing JSON.
        """
        return {"text_data": self.write(cloudevent).decode()}

    def decode(self, **kwargs: Unpack[ChannelEncoding]) -> BaseCloudEvent:
        """Decode JSON text data into a CloudEvent.

        Args:
            **kwargs: Must contain 'text_data' with JSON string.

        Returns:
            The decoded CloudEvent.

        Raises:
            ValueError: If no text_data is provided.
        """
        if text_data := kwargs.get("text_data"):
            return self.read(None, text_data)

        msg = "No text section for incoming WebSocket frame!"
        raise ValueError(msg)


def _get_preferred_subprotocol(servers: Sequence[Subprotocol], clients: Sequence[bytes]) -> Subprotocol | None:
    for c in clients:
        for s in servers:
            if s.accepts(c.decode()):
                return s

    return None


class CloudEventConsumer(WebsocketConsumer):
    """WebSocket consumer for handling CloudEvents synchronously.

    Extends WebsocketConsumer to provide CloudEvent encoding/decoding
    over WebSocket connections using specified subprotocols.
    """

    def __init__(self, subprotocols: Sequence[Subprotocol] | None = None) -> None:
        """Initialize the consumer with optional subprotocols.

        Args:
            subprotocols: Sequence of Subprotocol instances to support.
                Defaults to an empty list.
        """
        if subprotocols is None:
            subprotocols = []
        self.subprotocols = subprotocols
        self.protocol: Subprotocol | None = None

    @override
    def accept(self, subprotocol: str | None = None, headers: list[tuple[str, str]] | None = None) -> None:
        """Accept the WebSocket connection with optional subprotocol.

        If no subprotocol is provided but one is negotiated, use it.

        Args:
            subprotocol: The subprotocol to accept.
            headers: Optional headers for the acceptance.
        """
        if subprotocol is None and self.protocol:
            subprotocol = self.protocol.subprotocol

        return super().accept(subprotocol, headers)

    @override
    def websocket_connect(self, message: WebSocketConnectEvent) -> None:
        """Handle WebSocket connection establishment and subprotocol negotiation.

        Adds the consumer to channel groups, negotiates the subprotocol
        based on client headers, and calls connect() if a protocol is found.

        Args:
            message: The WebSocket connect event.

        Raises:
            InvalidChannelLayerError: If channel layer doesn't support groups.
        """
        for header, value in self.scope["headers"]:
            if header.lower() == SEC_WS_PROTOCOL:
                client_subprotocols = [v.strip() for v in value.split(b",")]
                self.protocol = _get_preferred_subprotocol(self.subprotocols, client_subprotocols)
                break

        if self.protocol:
            super().websocket_connect(message)
        else:
            self.close()

    @override
    def receive(self, text_data: str | None = None, bytes_data: bytes | None = None) -> None:
        """Receive WebSocket data and decode it as a CloudEvent.

        Args:
            text_data: Optional text data from the WebSocket.
            bytes_data: Optional bytes data from the WebSocket.
        """
        assert self.protocol  # noqa: S101
        self.receive_cloudevent(self.protocol.decode(text_data=text_data, bytes_data=bytes_data))

    def receive_cloudevent(self, cloudevent: BaseCloudEvent) -> None:
        """Process a received CloudEvent.

        Override this method to handle incoming CloudEvents.

        Args:
            cloudevent: The received CloudEvent.
        """

    def send_cloudevent(self, cloudevent: BaseCloudEvent, *, close: bool = False) -> None:
        """Encode and send a CloudEvent over the WebSocket.

        Args:
            cloudevent: The CloudEvent to send.
            close: Whether to close the connection after sending.
        """
        assert self.protocol  # noqa: S101
        super().send(**self.protocol.encode(cloudevent), close=close)


class AsyncCloudEventConsumer(AsyncWebsocketConsumer):
    """Asynchronous WebSocket consumer for handling CloudEvents.

    Extends AsyncWebsocketConsumer to provide CloudEvent encoding/decoding
    over WebSocket connections using specified subprotocols.
    """

    def __init__(self, subprotocols: Sequence[Subprotocol] | None = None) -> None:
        """Initialize the consumer with optional subprotocols.

        Args:
            subprotocols: Sequence of Subprotocol instances to support.
                Defaults to an empty list.
        """
        if subprotocols is None:
            subprotocols = []
        self.subprotocols = subprotocols
        self.protocol: Subprotocol | None = None

    @override
    async def accept(self, subprotocol: str | None = None, headers: list[tuple[str, str]] | None = None) -> None:
        """Accept the WebSocket connection with optional subprotocol.

        If no subprotocol is provided but one is negotiated, use it.

        Args:
            subprotocol: The subprotocol to accept.
            headers: Optional headers for the acceptance.
        """
        if subprotocol is None and self.protocol:
            subprotocol = self.protocol.subprotocol

        return await super().accept(subprotocol, headers)

    @override
    async def websocket_connect(self, message: WebSocketConnectEvent) -> None:
        """Handle WebSocket connection establishment and subprotocol negotiation.

        Adds the consumer to channel groups, negotiates the subprotocol
        based on client headers, and calls connect() if a protocol is found.

        Args:
            message: The WebSocket connect event.

        Raises:
            InvalidChannelLayerError: If channel layer doesn't support groups.
        """
        for header, value in self.scope["headers"]:
            if header.lower() == SEC_WS_PROTOCOL:
                client_subprotocols = [v.strip() for v in value.split(b",")]
                self.protocol = _get_preferred_subprotocol(self.subprotocols, client_subprotocols)
                break

        if self.protocol:
            await super().websocket_connect(message)
        else:
            await self.close()

    @override
    async def receive(self, text_data: str | None = None, bytes_data: bytes | None = None) -> None:
        """Receive WebSocket data and decode it as a CloudEvent.

        Args:
            text_data: Optional text data from the WebSocket.
            bytes_data: Optional bytes data from the WebSocket.
        """
        assert self.protocol  # noqa: S101
        await self.receive_cloudevent(self.protocol.decode(text_data=text_data, bytes_data=bytes_data))

    async def receive_cloudevent(self, cloudevent: BaseCloudEvent) -> None:
        """Process a received CloudEvent.

        Override this method to handle incoming CloudEvents.

        Args:
            cloudevent: The received CloudEvent.
        """

    async def send_cloudevent(self, cloudevent: BaseCloudEvent, *, close: bool = False) -> None:
        """Encode and send a CloudEvent over the WebSocket.

        Args:
            cloudevent: The CloudEvent to send.
            close: Whether to close the connection after sending.
        """
        assert self.protocol  # noqa: S101
        await super().send(**self.protocol.encode(cloudevent), close=close)
