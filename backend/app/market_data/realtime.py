import asyncio
import json
import logging
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from contextlib import AbstractAsyncContextManager
from datetime import datetime
from typing import Any, Protocol

from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed

from app.core.config import Settings
from app.market_data.schemas import RealtimeBar

_LOGGER = logging.getLogger(__name__)
_STREAM_BASE_URL = "wss://stream.data.alpaca.markets/v2"


class RealtimeStreamError(RuntimeError):
    """Raised when Alpaca's live market-data stream cannot be used safely."""


class RealtimeAuthenticationError(RealtimeStreamError):
    """Raised when Alpaca rejects the stream credentials or selected feed."""


class RealtimeRateLimitError(RealtimeStreamError):
    """Raised when Alpaca reports that a stream connection limit was reached."""


class AsyncMarketConnection(Protocol):
    async def send(self, message: str) -> None: ...

    async def recv(self) -> str: ...


ConnectionFactory = Callable[[str], AbstractAsyncContextManager[AsyncMarketConnection]]
Sleep = Callable[[float], Awaitable[None]]


class AlpacaRealtimeBarStream:
    """Consume ordered, de-duplicated minute bars from one Alpaca stock-data WebSocket."""

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        *,
        feed: str = "iex",
        max_reconnects: int = 5,
        reconnect_initial_seconds: float = 1.0,
        reconnect_max_seconds: float = 30.0,
        connection_factory: ConnectionFactory = connect,
        sleep: Sleep = asyncio.sleep,
    ) -> None:
        if not api_key or not secret_key:
            raise ValueError("ALPACA_API_KEY and ALPACA_SECRET_KEY must be configured")
        if feed not in {"iex", "sip"}:
            raise ValueError("Alpaca real-time feed must be iex or sip")
        if max_reconnects < 1:
            raise ValueError("max_reconnects must be at least 1")
        if reconnect_initial_seconds <= 0 or reconnect_max_seconds < reconnect_initial_seconds:
            raise ValueError("reconnect delays must be positive and ordered")
        self._api_key = api_key
        self._secret_key = secret_key
        self._feed = feed
        self._max_reconnects = max_reconnects
        self._reconnect_initial_seconds = reconnect_initial_seconds
        self._reconnect_max_seconds = reconnect_max_seconds
        self._connection_factory = connection_factory
        self._sleep = sleep

    @classmethod
    def from_settings(cls, settings: Settings) -> "AlpacaRealtimeBarStream":
        return cls(
            api_key=settings.alpaca_api_key or "",
            secret_key=settings.alpaca_secret_key or "",
            feed=settings.alpaca_data_feed,
        )

    @property
    def stream_url(self) -> str:
        return f"{_STREAM_BASE_URL}/{self._feed}"

    async def stream(self, symbols: Sequence[str]) -> AsyncIterator[RealtimeBar]:
        """Yield only new completed minute bars, reconnecting boundedly after transient failures."""
        normalized_symbols = _normalize_symbols(symbols)
        latest_timestamps: dict[str, datetime] = {}
        reconnects = 0

        while True:
            try:
                async with self._connection_factory(self.stream_url) as connection:
                    await self._authenticate(connection)
                    await connection.send(
                        json.dumps({"action": "subscribe", "bars": list(normalized_symbols)})
                    )
                    async for bar in self._bars(connection):
                        latest_timestamp = latest_timestamps.get(bar.symbol)
                        if latest_timestamp is not None and bar.timestamp <= latest_timestamp:
                            continue
                        latest_timestamps[bar.symbol] = bar.timestamp
                        reconnects = 0
                        yield bar
            except (ConnectionClosed, OSError, RealtimeRateLimitError) as error:
                if reconnects >= self._max_reconnects:
                    raise RealtimeStreamError(
                        f"Alpaca stream reconnect limit reached after {reconnects} retries"
                    ) from error
                delay = min(
                    self._reconnect_initial_seconds * (2**reconnects), self._reconnect_max_seconds
                )
                reconnects += 1
                _LOGGER.warning(
                    "realtime_stream_reconnecting",
                    extra={
                        "feed": self._feed,
                        "reason": type(error).__name__,
                        "delay_seconds": delay,
                        "reconnect_attempt": reconnects,
                    },
                )
                await self._sleep(delay)

    async def _authenticate(self, connection: AsyncMarketConnection) -> None:
        await connection.send(
            json.dumps({"action": "auth", "key": self._api_key, "secret": self._secret_key})
        )
        while True:
            messages = _parse_messages(await connection.recv())
            for message in messages:
                _raise_for_error_message(message)
                if message.get("T") == "success" and message.get("msg") == "authenticated":
                    return

    async def _bars(self, connection: AsyncMarketConnection) -> AsyncIterator[RealtimeBar]:
        while True:
            messages = _parse_messages(await connection.recv())
            for message in messages:
                _raise_for_error_message(message)
                if message.get("T") != "b":
                    continue
                try:
                    yield RealtimeBar(
                        symbol=message["S"],
                        timestamp=message["t"],
                        open=message["o"],
                        high=message["h"],
                        low=message["l"],
                        close=message["c"],
                        volume=message["v"],
                        source=f"alpaca:{self._feed}:stream",
                    )
                except (KeyError, TypeError, ValueError) as error:
                    raise RealtimeStreamError("Alpaca returned an invalid real-time bar") from error


def _normalize_symbols(symbols: Sequence[str]) -> tuple[str, ...]:
    normalized = tuple(symbol.strip().upper() for symbol in symbols if symbol.strip())
    if not normalized:
        raise ValueError("at least one non-blank symbol is required")
    if len(set(normalized)) != len(normalized):
        raise ValueError("real-time symbols must be unique")
    return normalized


def _parse_messages(raw_message: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(raw_message)
    except json.JSONDecodeError as error:
        raise RealtimeStreamError("Alpaca returned invalid WebSocket JSON") from error
    if not isinstance(payload, list) or not all(isinstance(message, dict) for message in payload):
        raise RealtimeStreamError("Alpaca returned an invalid WebSocket message batch")
    return payload


def _raise_for_error_message(message: dict[str, Any]) -> None:
    if message.get("T") != "error":
        return
    code = message.get("code")
    detail = message.get("msg")
    if code == 406:
        raise RealtimeRateLimitError("Alpaca stream connection limit reached")
    if code == 402:
        raise RealtimeAuthenticationError("Alpaca stream authentication failed")
    raise RealtimeStreamError(f"Alpaca stream error {code}: {detail}")
