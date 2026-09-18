from decimal import Decimal
from typing import Protocol

from sqlalchemy.orm import Session

from app.execution.broker import BrokerInterface
from app.execution.types import BrokerOrder, BrokerOrderRequest, BrokerSide
from app.observability.telemetry import get_telemetry
from app.risk.types import RiskDecision


class PaperTradingModelGate(Protocol):
    """Registry contract required before a model-driven paper order can reach a broker."""

    def require_paper_trading_eligibility(self, session: Session, model_version: str) -> object: ...


def broker_order_from_risk_decision(
    decision: RiskDecision, *, client_order_id: str | None = None
) -> BrokerOrderRequest:
    """Translate only an approved risk decision into the narrow broker-order contract."""
    if not decision.approved or decision.modified_order is None:
        raise ValueError("execution requires an approved risk decision with a modified order")
    order = decision.modified_order
    return BrokerOrderRequest(
        symbol=order.symbol,
        side=BrokerSide(order.side.value),
        quantity=Decimal(order.quantity),
        client_order_id=client_order_id,
    )


def submit_approved_order(
    broker: BrokerInterface,
    decision: RiskDecision,
    *,
    client_order_id: str | None = None,
    model_gate: PaperTradingModelGate | None = None,
    session: Session | None = None,
) -> BrokerOrder:
    """Submit an approved order, allowing model lineage only after registry approval."""
    lineage = decision.original_order.lineage
    if lineage is not None:
        if model_gate is None or session is None:
            raise ValueError(
                "model-driven paper execution requires a model registry gate and session"
            )
        model_gate.require_paper_trading_eligibility(session, lineage.model_version)
    order = broker.submit_order(
        broker_order_from_risk_decision(decision, client_order_id=client_order_id)
    )
    get_telemetry().record_trade(symbol=order.symbol, side=order.side.value)
    return order
