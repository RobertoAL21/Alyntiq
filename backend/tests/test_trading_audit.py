from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.audit.repository import TradingAuditError, store_trading_decision
from app.audit.service import TradingAuditService
from app.audit.types import AuditRiskDecision, AuditSignal, TradingDecision
from app.backtesting.types import SignalLineage, SignalSide
from app.risk.types import ProposedOrder, RiskDecision, RiskRule


def make_risk_decision(*, approved: bool = True) -> RiskDecision:
    proposal = ProposedOrder(
        timestamp=datetime(2024, 1, 2, 15, 30, tzinfo=UTC),
        symbol="aapl",
        side=SignalSide.BUY,
        quantity=5,
        lineage=SignalLineage(
            model_version="advanced-random-forest-v1",
            strategy_version="ml-threshold-v1",
            feature_version="features-v1",
            up_probability=0.72,
        ),
    )
    return RiskDecision(
        approved=approved,
        reason="approved" if approved else "maximum drawdown limit reached",
        rule=None if approved else RiskRule.MAXIMUM_DRAWDOWN,
        original_order=proposal,
        modified_order=proposal if approved else None,
    )


def test_audit_records_reconstruct_lineage_risk_order_and_execution(db_session: Session) -> None:
    service = TradingAuditService()
    recorded = service.record_risk_decision(
        db_session,
        make_risk_decision(),
        prediction=Decimal("0.72"),
        confidence=Decimal("0.72"),
    )
    db_session.commit()
    submitted = service.record_order_submission(
        db_session, decision_id=recorded.id, order_id="paper-order-123"
    )
    executed = service.record_execution(
        db_session,
        decision_id=recorded.id,
        order_id="paper-order-123",
        price=Decimal("101.25"),
        quantity=5,
    )
    db_session.commit()
    reloaded = service.get(db_session, recorded.id)

    assert recorded.symbol == "AAPL"
    assert recorded.model_version == "advanced-random-forest-v1"
    assert recorded.strategy_version == "ml-threshold-v1"
    assert recorded.feature_version == "features-v1"
    assert recorded.risk_decision is AuditRiskDecision.APPROVED
    assert submitted.executed is False
    assert executed.executed is True
    assert reloaded == executed
    assert reloaded.price == Decimal("101.25000000")
    assert reloaded.quantity == 5


def test_audit_execution_updates_are_idempotent_but_never_overwrite_history(
    db_session: Session,
) -> None:
    service = TradingAuditService()
    recorded = service.record_risk_decision(db_session, make_risk_decision())
    first = service.record_execution(
        db_session,
        decision_id=recorded.id,
        order_id="paper-order-123",
        price=Decimal("101"),
        quantity=5,
    )
    repeated = service.record_execution(
        db_session,
        decision_id=recorded.id,
        order_id="paper-order-123",
        price=Decimal("101"),
        quantity=5,
    )

    assert repeated == first
    with pytest.raises(TradingAuditError, match="different execution"):
        service.record_execution(
            db_session,
            decision_id=recorded.id,
            order_id="paper-order-123",
            price=Decimal("102"),
            quantity=5,
        )


def test_rejected_and_duplicate_decisions_cannot_be_linked_or_mutated(db_session: Session) -> None:
    service = TradingAuditService()
    rejected = service.record_risk_decision(db_session, make_risk_decision(approved=False))

    with pytest.raises(TradingAuditError, match="only an approved"):
        service.record_order_submission(
            db_session, decision_id=rejected.id, order_id="paper-order-123"
        )

    conflicting = TradingDecision(
        id=rejected.id,
        timestamp=rejected.timestamp,
        symbol=rejected.symbol,
        signal=AuditSignal.BUY,
        risk_decision=AuditRiskDecision.REJECTED,
        reason="a different reason",
        quantity=5,
    )
    with pytest.raises(TradingAuditError, match="different data"):
        store_trading_decision(db_session, conflicting)
