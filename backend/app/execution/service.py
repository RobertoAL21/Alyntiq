from decimal import Decimal

from app.execution.broker import BrokerInterface
from app.execution.types import BrokerOrder, BrokerOrderRequest, BrokerSide
from app.risk.types import RiskDecision


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
) -> BrokerOrder:
    """Submit an explicitly risk-approved order through the injected paper broker."""
    return broker.submit_order(
        broker_order_from_risk_decision(decision, client_order_id=client_order_id)
    )
