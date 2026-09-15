import asyncio
import json
from collections.abc import Sequence

import pytest

from app.market_data.realtime import (
    AlpacaRealtimeBarStream,
    RealtimeAuthenticationError,
)


class FakeConnection:
    def __init__(self, messages: Sequence[str | Exception]) -> None:
        self._messages = iter(messages)
        self.sent: list[str] = []
        self.closed = False

    async def __aenter__(self) -> "FakeConnection":
        return self

    async def __aexit__(self, *_: object) -> None:
        self.closed = True

    async def send(self, message: str) -> None:
        self.sent.append(message)

    async def recv(self) -> str:
        message = next(self._messages)
        if isinstance(message, Exception):
            raise message
        return message


class FakeConnectionFactory:
    def __init__(self, connections: Sequence[FakeConnection]) -> None:
        self._connections = iter(connections)
        self.urls: list[str] = []

    def __call__(self, url: str) -> FakeConnection:
        self.urls.append(url)
        return next(self._connections)


def batch(*messages: dict[str, object]) -> str:
    return json.dumps(list(messages))


def bar(timestamp: str) -> dict[str, object]:
    return {
        "T": "b",
        "S": "AAPL",
        "o": 100,
        "h": 102,
        "l": 99,
        "c": 101,
        "v": 10,
        "t": timestamp,
    }


async def collect(stream: AlpacaRealtimeBarStream, count: int) -> list:
    values = []
    async for value in stream.stream(["aapl"]):
        values.append(value)
        if len(values) == count:
            return values
    return values


def test_realtime_stream_authenticates_subscribes_and_drops_duplicate_or_out_of_order_bars() -> (
    None
):
    connection = FakeConnection(
        [
            batch({"T": "success", "msg": "connected"}),
            batch({"T": "success", "msg": "authenticated"}),
            batch({"T": "subscription", "bars": ["AAPL"]}),
            batch(
                bar("2024-01-02T15:30:00Z"),
                bar("2024-01-02T15:30:00Z"),
                bar("2024-01-02T15:29:00Z"),
                bar("2024-01-02T15:31:00Z"),
            ),
        ]
    )
    factory = FakeConnectionFactory([connection])
    stream = AlpacaRealtimeBarStream("key", "secret", connection_factory=factory)

    bars = asyncio.run(collect(stream, 2))

    assert [item.timestamp.isoformat() for item in bars] == [
        "2024-01-02T15:30:00+00:00",
        "2024-01-02T15:31:00+00:00",
    ]
    assert bars[0].source == "alpaca:iex:stream"
    assert bars[0].timeframe == "1Min"
    assert factory.urls == ["wss://stream.data.alpaca.markets/v2/iex"]
    assert json.loads(connection.sent[0]) == {"action": "auth", "key": "key", "secret": "secret"}
    assert json.loads(connection.sent[1]) == {"action": "subscribe", "bars": ["AAPL"]}
    assert connection.closed is True


def test_realtime_stream_reconnects_after_connection_errors_and_rate_limits() -> None:
    disconnected = FakeConnection(
        [
            batch({"T": "success", "msg": "connected"}),
            batch({"T": "success", "msg": "authenticated"}),
            OSError("network interrupted"),
        ]
    )
    rate_limited = FakeConnection(
        [
            batch({"T": "success", "msg": "connected"}),
            batch({"T": "error", "code": 406, "msg": "connection limit exceeded"}),
        ]
    )
    recovered = FakeConnection(
        [
            batch({"T": "success", "msg": "connected"}),
            batch({"T": "success", "msg": "authenticated"}),
            batch(bar("2024-01-02T15:30:00Z")),
        ]
    )
    factory = FakeConnectionFactory([disconnected, rate_limited, recovered])
    delays: list[float] = []

    async def record_sleep(delay: float) -> None:
        delays.append(delay)

    stream = AlpacaRealtimeBarStream(
        "key",
        "secret",
        max_reconnects=2,
        reconnect_initial_seconds=0.5,
        connection_factory=factory,
        sleep=record_sleep,
    )

    bars = asyncio.run(collect(stream, 1))

    assert len(bars) == 1
    assert delays == [0.5, 1.0]
    assert len(factory.urls) == 3


def test_realtime_stream_does_not_retry_authentication_or_protocol_errors() -> None:
    connection = FakeConnection(
        [
            batch({"T": "success", "msg": "connected"}),
            batch({"T": "error", "code": 402, "msg": "auth failed"}),
        ]
    )
    stream = AlpacaRealtimeBarStream(
        "key", "secret", connection_factory=FakeConnectionFactory([connection])
    )

    with pytest.raises(RealtimeAuthenticationError, match="authentication failed"):
        asyncio.run(collect(stream, 1))
