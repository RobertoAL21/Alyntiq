from decimal import Decimal

from sqlalchemy.orm import Session

from app.audit.repository import (
    TradingAuditError,
    load_trading_decision,
    record_execution,
    record_order_submission,
    store_trading_decision,
)
from app.audit.types import TradingDecision
from app.risk.types import RiskDecision


class TradingAuditService:
    """Coordinate explicit audit writes without embedding audit state in risk or execution."""

    def record_risk_decision(
        self,
        session: Session,
        risk_decision: RiskDecision,
        *,
        prediction: Decimal | None = None,
        confidence: Decimal | None = None,
    ) -> TradingDecision:
        decision = TradingDecision.from_risk_decision(
            risk_decision, prediction=prediction, confidence=confidence
        )
        return store_trading_decision(session, decision)

    def record_order_submission(
        self, session: Session, *, decision_id: str, order_id: str
    ) -> TradingDecision:
        return record_order_submission(session, decision_id=decision_id, order_id=order_id)

    def record_execution(
        self,
        session: Session,
        *,
        decision_id: str,
        order_id: str,
        price: Decimal,
        quantity: int,
    ) -> TradingDecision:
        return record_execution(
            session,
            decision_id=decision_id,
            order_id=order_id,
            price=price,
            quantity=quantity,
        )

    def get(self, session: Session, decision_id: str) -> TradingDecision:
        return load_trading_decision(session, decision_id)


__all__ = ["TradingAuditError", "TradingAuditService"]
