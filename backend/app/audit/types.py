from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from app.risk.types import RiskDecision


class AuditSignal(StrEnum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class AuditRiskDecision(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    NOT_EVALUATED = "not_evaluated"


@dataclass(frozen=True)
class TradingDecision:
    """A complete, append-first record of one strategy/risk/execution decision lifecycle."""

    timestamp: datetime
    symbol: str
    signal: AuditSignal
    risk_decision: AuditRiskDecision
    reason: str
    model_version: str | None = None
    strategy_version: str | None = None
    feature_version: str | None = None
    prediction: Decimal | None = None
    confidence: Decimal | None = None
    order_id: str | None = None
    executed: bool = False
    price: Decimal | None = None
    quantity: int | None = None
    id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("trading decision timestamps must include a timezone")
        if not self.symbol.strip() or not self.reason.strip():
            raise ValueError("trading decision symbol and reason must not be blank")
        if not isinstance(self.signal, AuditSignal):
            raise ValueError("trading decision signal must be buy, sell, or hold")
        if not isinstance(self.risk_decision, AuditRiskDecision):
            raise ValueError("trading decision risk_decision is invalid")
        try:
            UUID(self.id)
        except ValueError as error:
            raise ValueError("trading decision id must be a UUID") from error
        for name in ("model_version", "strategy_version", "feature_version", "order_id"):
            value = getattr(self, name)
            if value is not None and not value.strip():
                raise ValueError(f"trading decision {name} must not be blank when supplied")
        prediction = _decimal_or_none(self.prediction, "prediction")
        confidence = _decimal_or_none(self.confidence, "confidence")
        price = _decimal_or_none(self.price, "price")
        if confidence is not None and not Decimal("0") <= confidence <= Decimal("1"):
            raise ValueError("trading decision confidence must be between zero and one")
        if price is not None and price <= 0:
            raise ValueError("trading decision price must be positive")
        if self.quantity is not None and self.quantity < 1:
            raise ValueError("trading decision quantity must be at least 1")
        if self.risk_decision is not AuditRiskDecision.APPROVED and self.order_id is not None:
            raise ValueError("only an approved decision may reference an order")
        if self.executed and (
            self.risk_decision is not AuditRiskDecision.APPROVED
            or self.order_id is None
            or price is None
            or self.quantity is None
        ):
            raise ValueError(
                "an execution requires an approved decision, order, price, and quantity"
            )
        if not self.executed and price is not None:
            raise ValueError("an unexecuted decision must not contain an execution price")
        object.__setattr__(self, "timestamp", self.timestamp.astimezone(UTC))
        object.__setattr__(self, "symbol", self.symbol.strip().upper())
        object.__setattr__(self, "reason", self.reason.strip())
        object.__setattr__(self, "prediction", prediction)
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "price", price)
        for name in ("model_version", "strategy_version", "feature_version", "order_id"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, value.strip())

    @classmethod
    def from_risk_decision(
        cls,
        decision: RiskDecision,
        *,
        prediction: Decimal | None = None,
        confidence: Decimal | None = None,
    ) -> "TradingDecision":
        """Capture the strategy lineage and original proposal before broker submission."""
        proposal = decision.original_order
        lineage = proposal.lineage
        return cls(
            timestamp=proposal.timestamp,
            symbol=proposal.symbol,
            signal=AuditSignal(proposal.side.value),
            risk_decision=(
                AuditRiskDecision.APPROVED if decision.approved else AuditRiskDecision.REJECTED
            ),
            reason=decision.reason,
            model_version=None if lineage is None else lineage.model_version,
            strategy_version=None if lineage is None else lineage.strategy_version,
            feature_version=None if lineage is None else lineage.feature_version,
            prediction=prediction,
            confidence=confidence,
            quantity=(
                decision.original_order.quantity
                if decision.modified_order is None
                else decision.modified_order.quantity
            ),
        )


def _decimal_or_none(value: Decimal | None, name: str) -> Decimal | None:
    if value is None:
        return None
    try:
        decimal_value = Decimal(str(value))
    except (ArithmeticError, ValueError) as error:
        raise ValueError(f"trading decision {name} must be numeric") from error
    if not decimal_value.is_finite():
        raise ValueError(f"trading decision {name} must be finite")
    return decimal_value
