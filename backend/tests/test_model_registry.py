from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.backtesting.types import SignalLineage, SignalSide
from app.execution.service import submit_approved_order
from app.execution.types import BrokerOrder, BrokerSide
from app.model_registry.service import ModelLifecycleError, ModelRegistryService
from app.model_registry.types import ModelRegistration, ModelState
from app.risk.types import ProposedOrder, RiskDecision


def make_registration() -> ModelRegistration:
    return ModelRegistration(
        model_name="temporal transformer",
        model_version="temporal-transformer-v1",
        model_family="deep_learning",
        dataset_version="dataset-v1",
        feature_version="features-v1",
        target_version="targets-v1",
        parameters={"lookback": 20, "hidden_size": 16},
        metrics={"holdout_roc_auc": 0.61},
        backtest_results={"sharpe_ratio": 0.8, "number_of_trades": 12},
        artifact_uri="file:///mlruns/artifacts/temporal-transformer-v1",
    )


class RecordingBroker:
    def __init__(self) -> None:
        self.submissions = []

    def submit_order(self, request) -> BrokerOrder:
        self.submissions.append(request)
        return BrokerOrder(
            id="paper-order-1",
            client_order_id=request.client_order_id,
            symbol=request.symbol,
            side=BrokerSide(request.side),
            quantity=request.quantity,
            filled_quantity=Decimal("0"),
            status="accepted",
            submitted_at=datetime(2024, 1, 2, tzinfo=UTC),
        )


def make_model_risk_decision() -> RiskDecision:
    proposal = ProposedOrder(
        timestamp=datetime(2024, 1, 2, tzinfo=UTC),
        symbol="AAPL",
        side=SignalSide.BUY,
        quantity=2,
        lineage=SignalLineage(
            model_version="temporal-transformer-v1",
            strategy_version="ml-threshold-v1",
            feature_version="features-v1",
            up_probability=0.7,
        ),
    )
    return RiskDecision(True, "approved", None, proposal, proposal)


def test_registers_full_provenance_and_enforces_lifecycle_transitions(db_session: Session) -> None:
    service = ModelRegistryService()
    registration = make_registration()

    candidate = service.register(db_session, registration)
    repeated = service.register(db_session, registration)

    assert candidate.state is ModelState.CANDIDATE
    assert repeated == candidate
    assert candidate.registration.backtest_results["number_of_trades"] == 12
    with pytest.raises(ModelLifecycleError, match="cannot transition"):
        service.transition(
            db_session,
            model_version=registration.model_version,
            target_state=ModelState.PRODUCTION,
        )

    staging = service.transition(
        db_session,
        model_version=registration.model_version,
        target_state=ModelState.STAGING,
        now=datetime(2024, 1, 3, tzinfo=UTC),
    )
    production = service.transition(
        db_session,
        model_version=registration.model_version,
        target_state=ModelState.PRODUCTION,
        now=datetime(2024, 1, 4, tzinfo=UTC),
    )
    retired = service.transition(
        db_session,
        model_version=registration.model_version,
        target_state=ModelState.RETIRED,
        now=datetime(2024, 1, 5, tzinfo=UTC),
    )

    assert staging.state is ModelState.STAGING
    assert production.state is ModelState.PRODUCTION
    assert retired.state is ModelState.RETIRED
    assert retired.updated_at == datetime(2024, 1, 5, tzinfo=UTC)
    with pytest.raises(ModelLifecycleError, match="cannot transition"):
        service.transition(
            db_session,
            model_version=registration.model_version,
            target_state=ModelState.STAGING,
        )


def test_model_driven_paper_execution_requires_a_registered_production_model(
    db_session: Session,
) -> None:
    service = ModelRegistryService()
    service.register(db_session, make_registration())
    broker = RecordingBroker()
    decision = make_model_risk_decision()

    with pytest.raises(ValueError, match="requires a model registry gate"):
        submit_approved_order(broker, decision)
    with pytest.raises(ModelLifecycleError, match="not production"):
        submit_approved_order(broker, decision, model_gate=service, session=db_session)
    assert broker.submissions == []

    service.transition(
        db_session,
        model_version="temporal-transformer-v1",
        target_state=ModelState.STAGING,
    )
    service.transition(
        db_session,
        model_version="temporal-transformer-v1",
        target_state=ModelState.PRODUCTION,
    )

    submitted = submit_approved_order(broker, decision, model_gate=service, session=db_session)

    assert submitted.id == "paper-order-1"
    assert len(broker.submissions) == 1


def test_registration_rejects_missing_evidence_and_conflicting_versions(
    db_session: Session,
) -> None:
    with pytest.raises(ValueError, match="backtest_results"):
        ModelRegistration(
            **{
                **make_registration().__dict__,
                "backtest_results": {},
            }
        )

    service = ModelRegistryService()
    service.register(db_session, make_registration())
    conflicting = ModelRegistration(
        **{
            **make_registration().__dict__,
            "metrics": {"holdout_roc_auc": 0.62},
        }
    )
    with pytest.raises(ModelLifecycleError, match="different provenance"):
        service.register(db_session, conflicting)
