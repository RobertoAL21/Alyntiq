from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from app.backtesting.types import SignalLineage, SignalSide


class RiskRule(StrEnum):
    MAXIMUM_POSITION_SIZE = "maximum_position_size_pct"
    MAXIMUM_PORTFOLIO_EXPOSURE = "maximum_portfolio_exposure"
    MAXIMUM_DAILY_LOSS = "maximum_daily_loss"
    MAXIMUM_DRAWDOWN = "maximum_drawdown"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    MAX_TRADES_PER_DAY = "max_trades_per_day"
    MINIMUM_CASH_RESERVE = "minimum_cash_reserve"


@dataclass(frozen=True)
class ProposedOrder:
    """A strategy proposal before risk approval and before execution creates an order."""

    timestamp: datetime
    symbol: str
    side: SignalSide
    quantity: int
    lineage: SignalLineage | None = None

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("proposed order timestamps must include a timezone")
        if not self.symbol.strip():
            raise ValueError("proposed order symbol must not be blank")
        if not isinstance(self.side, SignalSide):
            raise ValueError("proposed order side must be buy or sell")
        if self.quantity < 1:
            raise ValueError("proposed order quantity must be at least 1")
        object.__setattr__(self, "timestamp", self.timestamp.astimezone(UTC))
        object.__setattr__(self, "symbol", self.symbol.strip().upper())


@dataclass(frozen=True)
class RiskContext:
    """Mark-to-market state supplied to risk without allowing it to execute an order."""

    timestamp: datetime
    symbol: str
    reference_price: Decimal
    equity: Decimal
    cash: Decimal
    position_quantity: int
    average_entry_price: Decimal | None
    daily_realized_pnl: Decimal
    current_drawdown: Decimal
    filled_orders_today: int

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("risk context timestamps must include a timezone")
        if not self.symbol.strip():
            raise ValueError("risk context symbol must not be blank")
        if self.reference_price <= 0 or self.equity <= 0:
            raise ValueError("risk context reference_price and equity must be positive")
        if self.cash < 0:
            raise ValueError("risk context cash must not be negative")
        if self.position_quantity < 0:
            raise ValueError("risk context position_quantity must not be negative")
        if self.position_quantity == 0 and self.average_entry_price is not None:
            raise ValueError("average_entry_price requires an open position")
        if self.position_quantity > 0 and (
            self.average_entry_price is None or self.average_entry_price <= 0
        ):
            raise ValueError("an open position requires a positive average_entry_price")
        if self.current_drawdown > 0:
            raise ValueError("current_drawdown must be zero or negative")
        if self.filled_orders_today < 0:
            raise ValueError("filled_orders_today must not be negative")
        object.__setattr__(self, "timestamp", self.timestamp.astimezone(UTC))
        object.__setattr__(self, "symbol", self.symbol.strip().upper())


@dataclass(frozen=True)
class RiskLimits:
    """Optional explicit risk limits; ``None`` disables the corresponding rule."""

    maximum_position_size_pct: Decimal | None = None
    maximum_portfolio_exposure: Decimal | None = None
    maximum_daily_loss_pct: Decimal | None = None
    maximum_drawdown_pct: Decimal | None = None
    stop_loss_pct: Decimal | None = None
    take_profit_pct: Decimal | None = None
    max_trades_per_day: int | None = None
    minimum_cash_reserve: Decimal | None = None

    def __post_init__(self) -> None:
        for name in (
            "maximum_position_size_pct",
            "maximum_portfolio_exposure",
            "maximum_daily_loss_pct",
            "maximum_drawdown_pct",
            "stop_loss_pct",
            "take_profit_pct",
        ):
            value = getattr(self, name)
            if value is not None and not Decimal("0") < value <= Decimal("1"):
                raise ValueError(f"{name} must be greater than zero and at most one")
        if self.max_trades_per_day is not None and self.max_trades_per_day < 1:
            raise ValueError("max_trades_per_day must be at least 1")
        if self.minimum_cash_reserve is not None and self.minimum_cash_reserve < 0:
            raise ValueError("minimum_cash_reserve must not be negative")


@dataclass(frozen=True)
class RiskDecision:
    """The independent result of evaluating a proposed order against configured limits."""

    approved: bool
    reason: str
    rule: RiskRule | None
    original_order: ProposedOrder
    modified_order: ProposedOrder | None
