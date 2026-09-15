import json
import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.core.config import Settings
from app.execution.types import (
    BrokerAccount,
    BrokerOrder,
    BrokerOrderRequest,
    BrokerOrderStatus,
    BrokerPosition,
    BrokerSide,
)

_PAPER_TRADING_URL = "https://paper-api.alpaca.markets/v2"
_LOGGER = logging.getLogger(__name__)


class PaperTradingSafetyError(RuntimeError):
    """Raised when an execution attempt is not explicitly configured for paper trading."""


class BrokerRequestError(RuntimeError):
    """Raised when Alpaca Paper Trading cannot complete or validate a broker request."""


class AlpacaPaperBroker:
    """Alpaca Trading API adapter permanently bound to the official paper endpoint."""

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        *,
        trading_environment: str = "paper",
        timeout_seconds: float = 30.0,
    ) -> None:
        if trading_environment != "paper":
            raise PaperTradingSafetyError("paper broker requires TRADING_ENVIRONMENT=paper")
        if not api_key or not secret_key:
            raise ValueError("ALPACA_API_KEY and ALPACA_SECRET_KEY must be configured")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._api_key = api_key
        self._secret_key = secret_key
        self._timeout_seconds = timeout_seconds

    @classmethod
    def from_settings(cls, settings: Settings) -> "AlpacaPaperBroker":
        return cls(
            api_key=settings.alpaca_api_key or "",
            secret_key=settings.alpaca_secret_key or "",
            trading_environment=settings.trading_environment,
        )

    def submit_order(self, order: BrokerOrderRequest) -> BrokerOrder:
        """Submit one whole-share market/day order to Alpaca's paper endpoint."""
        payload: dict[str, str] = {
            "symbol": order.symbol,
            "qty": _decimal_string(order.quantity),
            "side": order.side.value,
            "type": "market",
            "time_in_force": "day",
        }
        if order.client_order_id is not None:
            payload["client_order_id"] = order.client_order_id
        response = self._request("POST", "/orders", body=payload, expected_statuses={200})
        submitted = _parse_order(_require_mapping(response, "order response"))
        _LOGGER.info(
            "paper_order_submitted",
            extra={
                "order_id": submitted.id,
                "symbol": submitted.symbol,
                "side": submitted.side.value,
            },
        )
        return submitted

    def cancel_order(self, order_id: str) -> None:
        normalized_order_id = order_id.strip()
        if not normalized_order_id:
            raise ValueError("order_id must not be blank")
        self._request("DELETE", f"/orders/{normalized_order_id}", expected_statuses={204})
        _LOGGER.info("paper_order_cancelled", extra={"order_id": normalized_order_id})

    def get_positions(self) -> tuple[BrokerPosition, ...]:
        response = self._request("GET", "/positions", expected_statuses={200})
        raw_positions = _require_list(response, "positions response")
        return tuple(
            _parse_position(_require_mapping(position, "position")) for position in raw_positions
        )

    def get_account(self) -> BrokerAccount:
        response = self._request("GET", "/account", expected_statuses={200})
        return _parse_account(_require_mapping(response, "account response"))

    def get_orders(
        self, status: BrokerOrderStatus = BrokerOrderStatus.ALL, limit: int = 100
    ) -> tuple[BrokerOrder, ...]:
        if not isinstance(status, BrokerOrderStatus):
            raise ValueError("order status must be open, closed, or all")
        if not 1 <= limit <= 500:
            raise ValueError("order limit must be between 1 and 500")
        query = urlencode({"status": status.value, "limit": str(limit)})
        response = self._request("GET", f"/orders?{query}", expected_statuses={200})
        raw_orders = _require_list(response, "orders response")
        return tuple(_parse_order(_require_mapping(order, "order")) for order in raw_orders)

    def _request(
        self,
        method: str,
        path: str,
        *,
        expected_statuses: set[int],
        body: dict[str, str] | None = None,
    ) -> Any:
        data = None if body is None else json.dumps(body).encode("utf-8")
        headers = {
            "APCA-API-KEY-ID": self._api_key,
            "APCA-API-SECRET-KEY": self._secret_key,
            "Accept": "application/json",
        }
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = Request(f"{_PAPER_TRADING_URL}{path}", data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:  # noqa: S310
                status = response.status
                raw_payload = response.read()
        except HTTPError as error:
            raise BrokerRequestError(
                f"Alpaca paper request failed with status {error.code}"
            ) from error
        except URLError as error:
            raise BrokerRequestError("Alpaca paper request could not be reached") from error
        if status not in expected_statuses:
            raise BrokerRequestError(f"Alpaca paper request returned unexpected status {status}")
        if not raw_payload:
            return None
        try:
            return json.loads(raw_payload)
        except json.JSONDecodeError as error:
            raise BrokerRequestError("Alpaca paper returned invalid JSON") from error


def _parse_order(payload: dict[str, Any]) -> BrokerOrder:
    return BrokerOrder(
        id=_required_string(payload, "id"),
        client_order_id=_optional_string(payload, "client_order_id"),
        symbol=_required_string(payload, "symbol"),
        side=_parse_side(_required_string(payload, "side")),
        quantity=_required_decimal(payload, "qty"),
        filled_quantity=_required_decimal(payload, "filled_qty"),
        status=_required_string(payload, "status"),
        submitted_at=_parse_timestamp(_required_string(payload, "submitted_at")),
    )


def _parse_account(payload: dict[str, Any]) -> BrokerAccount:
    return BrokerAccount(
        id=_required_string(payload, "id"),
        cash=_required_decimal(payload, "cash"),
        equity=_required_decimal(payload, "equity"),
        buying_power=_required_decimal(payload, "buying_power"),
        currency=_required_string(payload, "currency"),
    )


def _parse_position(payload: dict[str, Any]) -> BrokerPosition:
    return BrokerPosition(
        symbol=_required_string(payload, "symbol"),
        quantity=_required_decimal(payload, "qty"),
        average_entry_price=_required_decimal(payload, "avg_entry_price"),
        market_value=_required_decimal(payload, "market_value"),
        unrealized_pnl=_required_decimal(payload, "unrealized_pl"),
    )


def _require_mapping(value: Any, description: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BrokerRequestError(f"Alpaca paper returned an invalid {description}")
    return value


def _require_list(value: Any, description: str) -> list[Any]:
    if not isinstance(value, list):
        raise BrokerRequestError(f"Alpaca paper returned an invalid {description}")
    return value


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise BrokerRequestError(f"Alpaca paper returned an invalid {key}")
    return value


def _optional_string(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise BrokerRequestError(f"Alpaca paper returned an invalid {key}")
    return value


def _required_decimal(payload: dict[str, Any], key: str) -> Decimal:
    value = payload.get(key)
    try:
        return Decimal(str(value))
    except (ArithmeticError, ValueError) as error:
        raise BrokerRequestError(f"Alpaca paper returned an invalid {key}") from error


def _parse_side(value: str) -> BrokerSide:
    try:
        return BrokerSide(value)
    except ValueError as error:
        raise BrokerRequestError("Alpaca paper returned an invalid order side") from error


def _parse_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise BrokerRequestError("Alpaca paper returned an invalid submitted_at") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise BrokerRequestError("Alpaca paper submitted_at must include a timezone")
    return parsed.astimezone(UTC)


def _decimal_string(value: Decimal) -> str:
    return format(value, "f")
