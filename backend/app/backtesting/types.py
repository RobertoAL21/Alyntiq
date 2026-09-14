from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Protocol


class SignalSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(StrEnum):
    PENDING = "pending"
    FILLED = "filled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class SignalLineage:
    """Version lineage and probability that caused a model-driven strategy proposal."""

    model_version: str
    strategy_version: str
    feature_version: str
    up_probability: float

    def __post_init__(self) -> None:
        if not self.model_version.strip():
            raise ValueError("model_version must not be blank")
        if not self.strategy_version.strip():
            raise ValueError("strategy_version must not be blank")
        if not self.feature_version.strip():
            raise ValueError("feature_version must not be blank")
        if not 0 <= self.up_probability <= 1:
            raise ValueError("up_probability must be between 0 and 1")


@dataclass(frozen=True)
class BacktestBar:
    """One fully formed historical OHLC bar available to a backtest strategy."""

    timestamp: datetime
    symbol: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("backtest bar timestamps must include a timezone")
        if not self.symbol.strip():
            raise ValueError("backtest bar symbol must not be blank")
        if min(self.open, self.high, self.low, self.close) <= 0:
            raise ValueError("backtest bar prices must be positive")
        if not self.low <= self.open <= self.high or not self.low <= self.close <= self.high:
            raise ValueError("backtest bar OHLC prices are inconsistent")
        object.__setattr__(self, "timestamp", self.timestamp.astimezone(UTC))
        object.__setattr__(self, "symbol", self.symbol.strip().upper())


@dataclass(frozen=True)
class Signal:
    """A strategy proposal, created after observing a completed historical bar."""

    timestamp: datetime
    symbol: str
    side: SignalSide
    quantity: int
    lineage: SignalLineage | None = None

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("signal timestamps must include a timezone")
        if not self.symbol.strip():
            raise ValueError("signal symbol must not be blank")
        if not isinstance(self.side, SignalSide):
            raise ValueError("signal side must be buy or sell")
        if self.quantity < 1:
            raise ValueError("signal quantity must be at least 1")
        object.__setattr__(self, "timestamp", self.timestamp.astimezone(UTC))
        object.__setattr__(self, "symbol", self.symbol.strip().upper())


@dataclass(frozen=True)
class Order:
    """An order created from a signal and scheduled for the next available bar open."""

    id: str
    created_at: datetime
    symbol: str
    side: SignalSide
    quantity: int
    status: OrderStatus
    rejection_reason: str | None = None
    lineage: SignalLineage | None = None


@dataclass(frozen=True)
class Fill:
    """A simulated execution at a valid future historical-bar opening price."""

    id: str
    order_id: str
    timestamp: datetime
    symbol: str
    side: SignalSide
    quantity: int
    price: Decimal
    commission: Decimal
    lineage: SignalLineage | None = None

    @property
    def notional(self) -> Decimal:
        return self.price * self.quantity


@dataclass(frozen=True)
class Position:
    """A single long position with its remaining entry commission allocation."""

    symbol: str
    quantity: int
    average_entry_price: Decimal
    opened_at: datetime
    entry_commission: Decimal
    entry_lineage: SignalLineage | None = None


@dataclass(frozen=True)
class Portfolio:
    """The cash, current position, and realized PnL of a Phase 7 single-asset backtest."""

    initial_cash: Decimal
    cash: Decimal
    position: Position | None
    realized_pnl: Decimal


@dataclass(frozen=True)
class Trade:
    """A closed quantity from the current long position."""

    id: str
    symbol: str
    quantity: int
    entry_timestamp: datetime
    exit_timestamp: datetime
    entry_price: Decimal
    exit_price: Decimal
    entry_commission: Decimal
    exit_commission: Decimal
    gross_pnl: Decimal
    net_pnl: Decimal
    entry_lineage: SignalLineage | None = None
    exit_lineage: SignalLineage | None = None


@dataclass(frozen=True)
class EquityPoint:
    timestamp: datetime
    cash: Decimal
    position_market_value: Decimal
    equity: Decimal


@dataclass(frozen=True)
class BacktestConfig:
    """Explicit research assumptions for capital, costs, and annualization."""

    initial_cash: Decimal = Decimal("100000")
    commission_rate: Decimal = Decimal("0")
    slippage_bps: Decimal = Decimal("0")
    trading_days_per_year: int = 252

    def __post_init__(self) -> None:
        if self.initial_cash <= 0:
            raise ValueError("initial_cash must be positive")
        if self.commission_rate < 0:
            raise ValueError("commission_rate must not be negative")
        if self.slippage_bps < 0:
            raise ValueError("slippage_bps must not be negative")
        if self.slippage_bps >= Decimal("10000"):
            raise ValueError("slippage_bps must be less than 10000")
        if self.trading_days_per_year < 1:
            raise ValueError("trading_days_per_year must be at least 1")


@dataclass(frozen=True)
class BacktestMetrics:
    total_return: float
    annualized_return: float | None
    cagr: float | None
    sharpe_ratio: float | None
    sortino_ratio: float | None
    max_drawdown: float
    volatility: float | None
    win_rate: float | None
    profit_factor: float | None
    number_of_trades: int
    average_trade: float | None
    best_trade: float | None
    worst_trade: float | None


@dataclass(frozen=True)
class BacktestResult:
    config: BacktestConfig
    portfolio: Portfolio
    orders: tuple[Order, ...]
    fills: tuple[Fill, ...]
    trades: tuple[Trade, ...]
    equity_curve: tuple[EquityPoint, ...]
    metrics: BacktestMetrics


class Strategy(Protocol):
    """Phase 8 strategy implementations emit at most one signal for each completed bar."""

    def on_bar(self, bar: BacktestBar, portfolio: Portfolio) -> Signal | None: ...
