import json
from typing import Any
from unittest import mock

import pytest
from channels.exceptions import AcceptConnection, DenyConnection
from cloudevents.core.v1.event import CloudEvent
from django.core.serializers.json import DjangoJSONEncoder

from django_cloudevents.contrib.channels import AsyncCloudEventConsumer, CloudEventConsumer, JSONSubprotocol


class TestJSONSubprotocol:
    def test_accepts(self) -> None:
        protocol = JSONSubprotocol()
        assert protocol.accepts("cloudevents.json")
        assert not protocol.accepts("unknown")

    def test_encode(self, cloudevent: dict[str, Any]) -> None:
        protocol = JSONSubprotocol()
        data = cloudevent.pop("data")
        event = CloudEvent(attributes=cloudevent, data=data)
        encoded = protocol.encode(event)
        assert "text_data" in encoded
        assert isinstance(encoded["text_data"], str)

    def test_decode(self, cloudevent: dict[str, Any]) -> None:
        protocol = JSONSubprotocol()
        decoded = protocol.decode(text_data=json.dumps(cloudevent, cls=DjangoJSONEncoder))
        assert isinstance(decoded, CloudEvent)

    def test_decode_no_text_data(self) -> None:
        protocol = JSONSubprotocol()
        with pytest.raises(ValueError, match="No text section"):
            protocol.decode()


class TestCloudEventConsumer:
    def test_init(self) -> None:
        consumer = CloudEventConsumer()
        assert consumer.subprotocols == []
        assert consumer.protocol is None

    def test_init_with_subprotocols(self) -> None:
        protocols = [JSONSubprotocol()]
        consumer = CloudEventConsumer(protocols)
        assert consumer.subprotocols == protocols

    def test_accept_without_protocol(self) -> None:
        consumer = CloudEventConsumer()
        with mock.patch("channels.generic.websocket.WebsocketConsumer.accept") as mock_super_accept:
            consumer.accept("test")
            mock_super_accept.assert_called_once_with("test", None)

    def test_accept_with_protocol(self) -> None:
        consumer = CloudEventConsumer()
        consumer.protocol = JSONSubprotocol()
        with mock.patch("channels.generic.websocket.WebsocketConsumer.accept") as mock_super_accept:
            consumer.accept(None)
            mock_super_accept.assert_called_once_with("cloudevents.json", None)

    def test_websocket_connect_no_protocol(self) -> None:
        consumer = CloudEventConsumer([JSONSubprotocol()])
        consumer.scope = {"headers": [(b"sec-websocket-protocol", b"unknown")]}
        consumer.groups = []
        with mock.patch.object(consumer, "close") as mock_close:
            consumer.websocket_connect(mock.MagicMock())
            mock_close.assert_called_once()

    def test_websocket_connect_with_protocol_accept(self) -> None:
        consumer = CloudEventConsumer([JSONSubprotocol()])
        consumer.scope = {"headers": [(b"sec-websocket-protocol", b"cloudevents.json")]}
        consumer.groups = []
        with (
            mock.patch.object(consumer, "connect", side_effect=AcceptConnection()) as mock_connect,
            mock.patch.object(consumer, "accept") as mock_accept,
        ):
            consumer.websocket_connect(mock.MagicMock())
            mock_connect.assert_called_once()
            mock_accept.assert_called_once()

    def test_websocket_connect_with_protocol_deny(self) -> None:
        consumer = CloudEventConsumer([JSONSubprotocol()])
        consumer.scope = {"headers": [(b"sec-websocket-protocol", b"cloudevents.json")]}
        consumer.groups = []
        with (
            mock.patch.object(consumer, "connect", side_effect=DenyConnection()) as mock_connect,
            mock.patch.object(consumer, "close") as mock_close,
        ):
            consumer.websocket_connect(mock.MagicMock())
            mock_connect.assert_called_once()
            mock_close.assert_called_once()

    def test_receive(self) -> None:
        consumer = CloudEventConsumer()
        consumer.protocol = JSONSubprotocol()
        with (
            mock.patch.object(consumer.protocol, "decode") as mock_decode,
            mock.patch.object(consumer, "receive_cloudevent") as mock_receive_cloudevent,
        ):
            mock_decode.return_value = mock.MagicMock()
            consumer.receive(text_data="test")
            mock_decode.assert_called_once_with(text_data="test", bytes_data=None)
            mock_receive_cloudevent.assert_called_once()

    def test_send_cloudevent(self) -> None:
        consumer = CloudEventConsumer()
        consumer.protocol = JSONSubprotocol()
        event = mock.MagicMock()
        with (
            mock.patch.object(consumer.protocol, "encode") as mock_encode,
            mock.patch("channels.generic.websocket.WebsocketConsumer.send") as mock_super_send,
        ):
            mock_encode.return_value = {"text_data": "encoded"}
            consumer.send_cloudevent(event)
            mock_encode.assert_called_once_with(event)
            mock_super_send.assert_called_once_with(text_data="encoded", close=False)


class TestAsyncCloudEventConsumer:
    def test_init(self) -> None:
        consumer = AsyncCloudEventConsumer()
        assert consumer.subprotocols == []
        assert consumer.protocol is None

    def test_init_with_subprotocols(self) -> None:
        protocols = [JSONSubprotocol()]
        consumer = AsyncCloudEventConsumer(protocols)
        assert consumer.subprotocols == protocols

    @pytest.mark.asyncio
    async def test_accept_without_protocol(self) -> None:
        consumer = AsyncCloudEventConsumer()
        with mock.patch("channels.generic.websocket.AsyncWebsocketConsumer.accept") as mock_super_accept:
            await consumer.accept("test")
            mock_super_accept.assert_called_once_with("test", None)

    @pytest.mark.asyncio
    async def test_accept_with_protocol(self) -> None:
        consumer = AsyncCloudEventConsumer()
        consumer.protocol = JSONSubprotocol()
        with mock.patch("channels.generic.websocket.AsyncWebsocketConsumer.accept") as mock_super_accept:
            await consumer.accept(None)
            mock_super_accept.assert_called_once_with("cloudevents.json", None)

    @pytest.mark.asyncio
    async def test_websocket_connect_no_protocol(self) -> None:
        consumer = AsyncCloudEventConsumer([JSONSubprotocol()])
        consumer.scope = {"headers": [(b"sec-websocket-protocol", b"unknown")]}
        consumer.groups = []
        with mock.patch.object(consumer, "close") as mock_close:
            await consumer.websocket_connect(mock.MagicMock())
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_connect_with_protocol_accept(self) -> None:
        consumer = AsyncCloudEventConsumer([JSONSubprotocol()])
        consumer.scope = {"headers": [(b"sec-websocket-protocol", b"cloudevents.json")]}
        consumer.groups = []
        with (
            mock.patch.object(consumer, "connect", side_effect=AcceptConnection()) as mock_connect,
            mock.patch.object(consumer, "accept") as mock_accept,
        ):
            await consumer.websocket_connect(mock.MagicMock())
            mock_connect.assert_called_once()
            mock_accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_connect_with_protocol_deny(self) -> None:
        consumer = AsyncCloudEventConsumer([JSONSubprotocol()])
        consumer.scope = {"headers": [(b"sec-websocket-protocol", b"cloudevents.json")]}
        consumer.groups = []
        with (
            mock.patch.object(consumer, "connect", side_effect=DenyConnection()) as mock_connect,
            mock.patch.object(consumer, "close") as mock_close,
        ):
            await consumer.websocket_connect(mock.MagicMock())
            mock_connect.assert_called_once()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_receive(self) -> None:
        consumer = AsyncCloudEventConsumer()
        consumer.protocol = JSONSubprotocol()
        with (
            mock.patch.object(consumer.protocol, "decode") as mock_decode,
            mock.patch.object(consumer, "receive_cloudevent") as mock_receive_cloudevent,
        ):
            mock_decode.return_value = mock.MagicMock()
            await consumer.receive(text_data="test")
            mock_decode.assert_called_once_with(text_data="test", bytes_data=None)
            mock_receive_cloudevent.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_cloudevent(self) -> None:
        consumer = AsyncCloudEventConsumer()
        consumer.protocol = JSONSubprotocol()
        event = mock.MagicMock()
        with (
            mock.patch.object(consumer.protocol, "encode") as mock_encode,
            mock.patch("channels.generic.websocket.AsyncWebsocketConsumer.send") as mock_super_send,
        ):
            mock_encode.return_value = {"text_data": "encoded"}
            await consumer.send_cloudevent(event)
            mock_encode.assert_called_once_with(event)
            mock_super_send.assert_called_once_with(text_data="encoded", close=False)
