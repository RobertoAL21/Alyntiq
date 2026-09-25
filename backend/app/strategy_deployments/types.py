from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum

from app.risk.types import RiskLimits


class StrategyDeploymentState(StrEnum):
    DRAFT = "draft"
    VALIDATED = "validated"
    ARMED = "armed"


@dataclass(frozen=True)
class StrategyDeploymentSpec:
    """Immutable intent that a future worker may consume after separate implementation."""

    name: str
    model_version: str
    strategy_version: str
    feature_version: str
    target_version: str
    source: str
    timeframe: str
    symbols: tuple[str, ...]
    buy_threshold: Decimal
    sell_threshold: Decimal
    order_quantity: int
    risk_limits: RiskLimits

    def __post_init__(self) -> None:
        for field_name, maximum_length in (
            ("name", 96),
            ("model_version", 64),
            ("strategy_version", 64),
            ("feature_version", 64),
            ("target_version", 64),
            ("source", 32),
            ("timeframe", 8),
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must not be blank")
            normalized = value.strip()
            if len(normalized) > maximum_length:
                raise ValueError(f"{field_name} is too long")
            object.__setattr__(self, field_name, normalized)

        if not self.symbols:
            raise ValueError("symbols must not be empty")
        normalized_symbols = tuple(_normalize_symbol(symbol) for symbol in self.symbols)
        if len(set(normalized_symbols)) != len(normalized_symbols):
            raise ValueError("symbols must not contain duplicates")
        object.__setattr__(self, "symbols", normalized_symbols)

        buy_threshold = _decimal(self.buy_threshold, "buy_threshold")
        sell_threshold = _decimal(self.sell_threshold, "sell_threshold")
        if not Decimal("0") <= sell_threshold < buy_threshold <= Decimal("1"):
            raise ValueError("thresholds must satisfy 0 <= sell_threshold < buy_threshold <= 1")
        object.__setattr__(self, "buy_threshold", buy_threshold)
        object.__setattr__(self, "sell_threshold", sell_threshold)

        if (
            isinstance(self.order_quantity, bool)
            or not isinstance(self.order_quantity, int)
            or self.order_quantity < 1
        ):
            raise ValueError("order_quantity must be at least 1")
        if not isinstance(self.risk_limits, RiskLimits):
            raise ValueError("risk_limits must be a RiskLimits instance")
        _require_all_risk_limits(self.risk_limits)


@dataclass(frozen=True)
class StrategyDeployment:
    id: str
    state: StrategyDeploymentState
    spec: StrategyDeploymentSpec
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("deployment id must not be blank")
        if not isinstance(self.state, StrategyDeploymentState):
            raise ValueError("deployment state is invalid")
        for field_name in ("created_at", "updated_at"):
            value = getattr(self, field_name)
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{field_name} must include a timezone")
            object.__setattr__(self, field_name, value.astimezone(UTC))


def _normalize_symbol(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("symbol must not be blank")
    normalized = value.strip().upper()
    if len(normalized) > 16:
        raise ValueError("symbol is too long")
    return normalized


def _decimal(value: Decimal, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a decimal")
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValueError(f"{field_name} must be a decimal") from error


def _require_all_risk_limits(limits: RiskLimits) -> None:
    for field_name in (
        "maximum_position_size_pct",
        "maximum_portfolio_exposure",
        "maximum_daily_loss_pct",
        "maximum_drawdown_pct",
        "stop_loss_pct",
        "take_profit_pct",
        "max_trades_per_day",
        "minimum_cash_reserve",
    ):
        if getattr(limits, field_name) is None:
            raise ValueError(f"risk_limits.{field_name} must be explicitly configured")
