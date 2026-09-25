from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.core.config import Settings
from app.model_registry.service import ModelRegistryService
from app.model_registry.types import ModelRegistration, ModelState
from app.risk.types import RiskLimits
from app.strategy_deployments.service import StrategyDeploymentError, StrategyDeploymentService
from app.strategy_deployments.types import StrategyDeploymentSpec, StrategyDeploymentState


def test_deployment_requires_production_model_matching_lineage_and_paper_environment(
    db_session,
) -> None:
    registry = ModelRegistryService()
    registry.register(db_session, _registration())
    service = StrategyDeploymentService(registry)
    deployment = service.create(db_session, _spec())

    with pytest.raises(StrategyDeploymentError, match="not production"):
        service.validate(
            db_session,
            deployment_id=deployment.id,
            settings=Settings(_env_file=None),
        )

    registry.transition(
        db_session,
        model_version="reviewed-v1",
        target_state=ModelState.STAGING,
        now=datetime(2026, 9, 24, tzinfo=UTC),
    )
    registry.transition(
        db_session,
        model_version="reviewed-v1",
        target_state=ModelState.PRODUCTION,
        now=datetime(2026, 9, 24, 1, tzinfo=UTC),
    )

    validated = service.validate(
        db_session,
        deployment_id=deployment.id,
        settings=Settings(_env_file=None),
        now=datetime(2026, 9, 24, 2, tzinfo=UTC),
    )
    armed = service.arm(
        db_session,
        deployment_id=deployment.id,
        settings=Settings(_env_file=None),
        now=datetime(2026, 9, 24, 3, tzinfo=UTC),
    )

    assert validated.state is StrategyDeploymentState.VALIDATED
    assert armed.state is StrategyDeploymentState.ARMED
    assert armed.spec.symbols == ("AAPL", "MSFT")

    with pytest.raises(StrategyDeploymentError, match="TRADING_ENVIRONMENT=paper"):
        service.arm(
            db_session,
            deployment_id=armed.id,
            settings=Settings(_env_file=None, TRADING_ENVIRONMENT="live"),
        )


def test_deployment_requires_every_risk_limit_and_a_valid_state_transition(db_session) -> None:
    registry = ModelRegistryService()
    registry.register(db_session, _registration())
    service = StrategyDeploymentService(registry)

    with pytest.raises(ValueError, match="maximum_drawdown_pct"):
        _spec(
            risk_limits=RiskLimits(
                maximum_position_size_pct=Decimal("0.10"),
                maximum_portfolio_exposure=Decimal("0.40"),
                maximum_daily_loss_pct=Decimal("0.03"),
                stop_loss_pct=Decimal("0.04"),
                take_profit_pct=Decimal("0.08"),
                max_trades_per_day=4,
                minimum_cash_reserve=Decimal("1000"),
            )
        )

    deployment = service.create(db_session, _spec())
    with pytest.raises(StrategyDeploymentError, match="validated deployment"):
        service.arm(
            db_session,
            deployment_id=deployment.id,
            settings=Settings(_env_file=None),
        )
    with pytest.raises(StrategyDeploymentError, match="only an armed"):
        service.disarm(db_session, deployment_id=deployment.id)


def test_deployment_rechecks_registry_lineage_when_arming(db_session) -> None:
    registry = ModelRegistryService()
    registry.register(db_session, _registration())
    registry.transition(
        db_session,
        model_version="reviewed-v1",
        target_state=ModelState.STAGING,
        now=datetime(2026, 9, 24, tzinfo=UTC),
    )
    registry.transition(
        db_session,
        model_version="reviewed-v1",
        target_state=ModelState.PRODUCTION,
        now=datetime(2026, 9, 24, 1, tzinfo=UTC),
    )
    service = StrategyDeploymentService(registry)
    deployment = service.create(db_session, _spec())
    validated = service.validate(
        db_session,
        deployment_id=deployment.id,
        settings=Settings(_env_file=None),
    )
    registry.transition(
        db_session,
        model_version="reviewed-v1",
        target_state=ModelState.STAGING,
        now=datetime(2026, 9, 24, 2, tzinfo=UTC),
    )

    with pytest.raises(StrategyDeploymentError, match="not production"):
        service.arm(
            db_session,
            deployment_id=validated.id,
            settings=Settings(_env_file=None),
        )


def _registration() -> ModelRegistration:
    return ModelRegistration(
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
    )


def _spec(risk_limits: RiskLimits | None = None) -> StrategyDeploymentSpec:
    return StrategyDeploymentSpec(
        name="Reviewed daily momentum",
        model_version="reviewed-v1",
        strategy_version="ml-strategy-v1",
        feature_version="features-v1",
        target_version="targets-v1",
        source="alpaca:iex:raw",
        timeframe="1D",
        symbols=("aapl", "MSFT"),
        buy_threshold=Decimal("0.60"),
        sell_threshold=Decimal("0.40"),
        order_quantity=10,
        risk_limits=risk_limits
        or RiskLimits(
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
