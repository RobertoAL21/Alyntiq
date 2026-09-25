from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select

from app.core.config import Settings
from app.db.models.trading_decision import TradingDecisionRecord
from app.model_registry.service import ModelRegistryService
from app.model_registry.types import ModelRegistration, ModelState
from app.paper_worker.repository import latest_preflights_by_deployment
from app.paper_worker.service import PaperWorkerService
from app.paper_worker.types import PaperWorkerPreflightOutcome
from app.risk.types import RiskLimits
from app.strategy_deployments.service import StrategyDeploymentService
from app.strategy_deployments.types import StrategyDeploymentSpec


def test_worker_preflights_only_armed_deployments_and_persists_ready_result(db_session) -> None:
    registry = _register_production_model(db_session)
    deployments = StrategyDeploymentService(registry)
    armed = _create_and_arm(db_session, deployments)
    deployments.create(db_session, _spec(name="Unarmed deployment"))

    results = PaperWorkerService(deployments).run_once(
        db_session,
        settings=Settings(_env_file=None),
        now=datetime(2026, 9, 25, tzinfo=UTC),
    )

    assert len(results) == 1
    assert results[0].deployment_id == armed.id
    assert results[0].outcome is PaperWorkerPreflightOutcome.READY
    assert latest_preflights_by_deployment(db_session, (armed.id,))[armed.id] == results[0]
    assert db_session.scalars(select(TradingDecisionRecord)).all() == []


def test_worker_blocks_an_armed_deployment_when_the_model_is_demoted(db_session) -> None:
    registry = _register_production_model(db_session)
    deployments = StrategyDeploymentService(registry)
    armed = _create_and_arm(db_session, deployments)
    registry.transition(
        db_session,
        model_version="reviewed-v1",
        target_state=ModelState.STAGING,
        now=datetime(2026, 9, 25, 1, tzinfo=UTC),
    )

    result = PaperWorkerService(deployments).run_once(
        db_session,
        settings=Settings(_env_file=None),
        now=datetime(2026, 9, 25, 2, tzinfo=UTC),
    )[0]

    assert result.deployment_id == armed.id
    assert result.outcome is PaperWorkerPreflightOutcome.BLOCKED
    assert "not production" in result.reason
    assert deployments.list(db_session)[0].state.value == "armed"


def _register_production_model(db_session) -> ModelRegistryService:
    registry = ModelRegistryService()
    registry.register(
        db_session,
        ModelRegistration(
            model_name="reviewed_model",
            model_version="reviewed-v1",
            model_family="baseline",
            dataset_version="dataset-v1",
            feature_version="features-v1",
            target_version="targets-v1",
            parameters={"seed": 7},
            metrics={"holdout_roc_auc": 0.61},
            backtest_results={"sharpe_ratio": 0.8},
            artifact_uri="file:///mlruns/artifacts/reviewed-v1",
        ),
    )
    registry.transition(
        db_session,
        model_version="reviewed-v1",
        target_state=ModelState.STAGING,
        now=datetime(2026, 9, 25, tzinfo=UTC),
    )
    registry.transition(
        db_session,
        model_version="reviewed-v1",
        target_state=ModelState.PRODUCTION,
        now=datetime(2026, 9, 25, tzinfo=UTC),
    )
    return registry


def _create_and_arm(db_session, deployments: StrategyDeploymentService):
    draft = deployments.create(db_session, _spec())
    deployments.validate(
        db_session,
        deployment_id=draft.id,
        settings=Settings(_env_file=None),
        now=datetime(2026, 9, 25, tzinfo=UTC),
    )
    return deployments.arm(
        db_session,
        deployment_id=draft.id,
        settings=Settings(_env_file=None),
        now=datetime(2026, 9, 25, tzinfo=UTC),
    )


def _spec(name: str = "Reviewed daily momentum") -> StrategyDeploymentSpec:
    return StrategyDeploymentSpec(
        name=name,
        model_version="reviewed-v1",
        strategy_version="ml-strategy-v1",
        feature_version="features-v1",
        target_version="targets-v1",
        source="alpaca:iex:raw",
        timeframe="1D",
        symbols=("AAPL",),
        buy_threshold=Decimal("0.60"),
        sell_threshold=Decimal("0.40"),
        order_quantity=10,
        risk_limits=RiskLimits(
            maximum_position_size_pct=Decimal("0.10"),
            maximum_portfolio_exposure=Decimal("0.40"),
            maximum_daily_loss_pct=Decimal("0.03"),
            maximum_drawdown_pct=Decimal("0.10"),
            stop_loss_pct=Decimal("0.04"),
            take_profit_pct=Decimal("0.08"),
            max_trades_per_day=4,
            minimum_cash_reserve=Decimal("1000"),
        ),
    )
