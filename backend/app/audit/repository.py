from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.audit.types import AuditRiskDecision, AuditSignal, TradingDecision
from app.db.models.trading_decision import TradingDecisionRecord


class TradingAuditError(ValueError):
    """Raised when an audit record would lose or contradict decision history."""


def store_trading_decision(session: Session, decision: TradingDecision) -> TradingDecision:
    """Persist a decision once; a duplicate UUID may only repeat identical immutable data."""
    existing = session.get(TradingDecisionRecord, decision.id)
    if existing is not None:
        if _to_decision(existing) != decision:
            raise TradingAuditError("trading decision id already records different data")
        return decision
    session.add(_to_record(decision))
    session.flush()
    return decision


def load_trading_decision(session: Session, decision_id: str) -> TradingDecision:
    record = session.get(TradingDecisionRecord, decision_id)
    if record is None:
        raise TradingAuditError("trading decision does not exist")
    return _to_decision(record)


def record_order_submission(
    session: Session, *, decision_id: str, order_id: str
) -> TradingDecision:
    """Attach one broker order to an approved decision without altering its original rationale."""
    record = _require_record(session, decision_id)
    if record.risk_decision != "approved":
        raise TradingAuditError("only an approved decision may receive an order id")
    normalized_order_id = order_id.strip()
    if not normalized_order_id:
        raise TradingAuditError("order_id must not be blank")
    if record.order_id is not None:
        if record.order_id == normalized_order_id:
            return _to_decision(record)
        raise TradingAuditError("trading decision already references a different order")
    record.order_id = normalized_order_id
    session.flush()
    return _to_decision(record)


def record_execution(
    session: Session,
    *,
    decision_id: str,
    order_id: str,
    price: Decimal,
    quantity: int,
) -> TradingDecision:
    """Record one fill outcome once; repeated identical reporting is safe and idempotent."""
    record = _require_record(session, decision_id)
    normalized_order_id = order_id.strip()
    if not normalized_order_id:
        raise TradingAuditError("order_id must not be blank")
    try:
        normalized_price = Decimal(str(price))
    except (ArithmeticError, ValueError) as error:
        raise TradingAuditError("execution price must be numeric") from error
    if normalized_price <= 0 or quantity < 1:
        raise TradingAuditError("execution price and quantity must be positive")
    if record.risk_decision != "approved":
        raise TradingAuditError("only an approved decision may be marked executed")
    if record.order_id is not None and record.order_id != normalized_order_id:
        raise TradingAuditError("trading decision already references a different order")
    if record.executed:
        if (
            record.order_id == normalized_order_id
            and record.price == normalized_price
            and record.quantity == quantity
        ):
            return _to_decision(record)
        raise TradingAuditError("trading decision already records a different execution")
    record.order_id = normalized_order_id
    record.executed = True
    record.price = normalized_price
    record.quantity = quantity
    session.flush()
    return _to_decision(record)


def _require_record(session: Session, decision_id: str) -> TradingDecisionRecord:
    record = session.get(TradingDecisionRecord, decision_id)
    if record is None:
        raise TradingAuditError("trading decision does not exist")
    return record


def _to_record(decision: TradingDecision) -> TradingDecisionRecord:
    return TradingDecisionRecord(
        id=decision.id,
        timestamp=decision.timestamp,
        symbol=decision.symbol,
        model_version=decision.model_version,
        strategy_version=decision.strategy_version,
        feature_version=decision.feature_version,
        prediction=decision.prediction,
        confidence=decision.confidence,
        signal=decision.signal.value,
        risk_decision=decision.risk_decision.value,
        order_id=decision.order_id,
        executed=decision.executed,
        price=decision.price,
        quantity=decision.quantity,
        reason=decision.reason,
    )


def _to_decision(record: TradingDecisionRecord) -> TradingDecision:
    return TradingDecision(
        id=record.id,
        timestamp=_as_utc(record.timestamp),
        symbol=record.symbol,
        model_version=record.model_version,
        strategy_version=record.strategy_version,
        feature_version=record.feature_version,
        prediction=record.prediction,
        confidence=record.confidence,
        signal=AuditSignal(record.signal),
        risk_decision=AuditRiskDecision(record.risk_decision),
        order_id=record.order_id,
        executed=record.executed,
        price=record.price,
        quantity=record.quantity,
        reason=record.reason,
    )


def _as_utc(timestamp: datetime) -> datetime:
    return timestamp.replace(tzinfo=UTC) if timestamp.tzinfo is None else timestamp.astimezone(UTC)
