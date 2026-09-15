from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum


class BrokerSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class BrokerOrderStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"
    ALL = "all"


@dataclass(frozen=True)
class BrokerOrderRequest:
    """A whole-share market order request for a broker adapter to submit."""

    symbol: str
    side: BrokerSide
    quantity: Decimal
    client_order_id: str | None = None

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("broker order symbol must not be blank")
        if not isinstance(self.side, BrokerSide):
            raise ValueError("broker order side must be buy or sell")
        try:
            quantity = Decimal(str(self.quantity))
        except (ArithmeticError, ValueError) as error:
            raise ValueError("broker order quantity must be numeric") from error
        if quantity <= 0:
            raise ValueError("broker order quantity must be positive")
        if quantity != quantity.to_integral_value():
            raise ValueError("Phase 12 broker orders require whole-share quantities")
        if self.client_order_id is not None and not self.client_order_id.strip():
            raise ValueError("client_order_id must not be blank when supplied")
        object.__setattr__(self, "symbol", self.symbol.strip().upper())
        object.__setattr__(self, "quantity", quantity)
        if self.client_order_id is not None:
            object.__setattr__(self, "client_order_id", self.client_order_id.strip())


@dataclass(frozen=True)
class BrokerOrder:
    id: str
    client_order_id: str | None
    symbol: str
    side: BrokerSide
    quantity: Decimal
    filled_quantity: Decimal
    status: str
    submitted_at: datetime

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.symbol.strip() or not self.status.strip():
            raise ValueError("broker order id, symbol, and status must not be blank")
        if self.quantity <= 0 or self.filled_quantity < 0:
            raise ValueError("broker order quantities are invalid")
        if self.filled_quantity > self.quantity:
            raise ValueError("filled_quantity must not exceed quantity")
        if self.submitted_at.tzinfo is None or self.submitted_at.utcoffset() is None:
            raise ValueError("broker order submitted_at must include a timezone")
        object.__setattr__(self, "symbol", self.symbol.strip().upper())
        object.__setattr__(self, "submitted_at", self.submitted_at.astimezone(UTC))


@dataclass(frozen=True)
class BrokerAccount:
    id: str
    cash: Decimal
    equity: Decimal
    buying_power: Decimal
    currency: str

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.currency.strip():
            raise ValueError("broker account id and currency must not be blank")
        if min(self.cash, self.equity, self.buying_power) < 0:
            raise ValueError("broker account balances must not be negative")
        object.__setattr__(self, "currency", self.currency.strip().upper())


@dataclass(frozen=True)
class BrokerPosition:
    symbol: str
    quantity: Decimal
    average_entry_price: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("broker position symbol must not be blank")
        if self.quantity == 0:
            raise ValueError("broker position quantity must not be zero")
        if self.average_entry_price <= 0:
            raise ValueError("broker position average_entry_price must be positive")
        object.__setattr__(self, "symbol", self.symbol.strip().upper())
