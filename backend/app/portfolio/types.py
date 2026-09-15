from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum


class PortfolioSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True)
class PortfolioFill:
    """An already-executed long-only fill that the portfolio ledger can account for."""

    id: str
    timestamp: datetime
    symbol: str
    side: PortfolioSide
    quantity: int
    price: Decimal
    commission: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("portfolio fill id must not be blank")
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("portfolio fill timestamps must include a timezone")
        if not self.symbol.strip():
            raise ValueError("portfolio fill symbol must not be blank")
        if not isinstance(self.side, PortfolioSide):
            raise ValueError("portfolio fill side must be buy or sell")
        if self.quantity < 1:
            raise ValueError("portfolio fill quantity must be at least 1")
        if self.price <= 0:
            raise ValueError("portfolio fill price must be positive")
        if self.commission < 0:
            raise ValueError("portfolio fill commission must not be negative")
        object.__setattr__(self, "timestamp", self.timestamp.astimezone(UTC))
        object.__setattr__(self, "symbol", self.symbol.strip().upper())

    @property
    def notional(self) -> Decimal:
        return self.price * self.quantity


@dataclass(frozen=True)
class PortfolioPosition:
    """A remaining long position and its unallocated entry commission."""

    symbol: str
    quantity: int
    average_entry_price: Decimal
    opened_at: datetime
    entry_commission: Decimal

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("portfolio position symbol must not be blank")
        if self.quantity < 1:
            raise ValueError("portfolio position quantity must be at least 1")
        if self.average_entry_price <= 0:
            raise ValueError("portfolio position average_entry_price must be positive")
        if self.opened_at.tzinfo is None or self.opened_at.utcoffset() is None:
            raise ValueError("portfolio position opened_at must include a timezone")
        if self.entry_commission < 0:
            raise ValueError("portfolio position entry_commission must not be negative")
        object.__setattr__(self, "symbol", self.symbol.strip().upper())
        object.__setattr__(self, "opened_at", self.opened_at.astimezone(UTC))


@dataclass(frozen=True)
class Portfolio:
    """Immutable multi-asset cash and long-position accounting state."""

    initial_cash: Decimal
    cash: Decimal
    positions: tuple[PortfolioPosition, ...]
    realized_pnl: Decimal

    def __post_init__(self) -> None:
        if self.initial_cash <= 0:
            raise ValueError("portfolio initial_cash must be positive")
        if self.cash < 0:
            raise ValueError("portfolio cash must not be negative")
        symbols = tuple(position.symbol for position in self.positions)
        if len(set(symbols)) != len(symbols):
            raise ValueError("portfolio positions must have unique symbols")
        if symbols != tuple(sorted(symbols)):
            raise ValueError("portfolio positions must be sorted by symbol")

    def position_for(self, symbol: str) -> PortfolioPosition | None:
        normalized_symbol = _normalize_symbol(symbol)
        return next(
            (position for position in self.positions if position.symbol == normalized_symbol), None
        )


@dataclass(frozen=True)
class PositionValuation:
    symbol: str
    quantity: int
    market_price: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    exposure_pct: Decimal


@dataclass(frozen=True)
class PortfolioValuation:
    """A completed-price mark of a portfolio, including PnL and long exposure."""

    timestamp: datetime
    cash: Decimal
    equity: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    gross_exposure_pct: Decimal
    positions: tuple[PositionValuation, ...]

    def position_for(self, symbol: str) -> PositionValuation | None:
        normalized_symbol = _normalize_symbol(symbol)
        return next(
            (position for position in self.positions if position.symbol == normalized_symbol), None
        )


@dataclass(frozen=True)
class PositionSize:
    """Whole-share buy quantity implied by a fixed percentage of marked equity."""

    symbol: str
    target_equity_pct: Decimal
    target_notional: Decimal
    current_notional: Decimal
    quantity: int
    limited_by_cash: bool


def _normalize_symbol(symbol: str) -> str:
    if not symbol.strip():
        raise ValueError("symbol must not be blank")
    return symbol.strip().upper()
