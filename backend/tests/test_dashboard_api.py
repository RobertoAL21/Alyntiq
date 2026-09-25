from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes import dashboard as dashboard_route
from app.dashboard.service import ExperimentRun
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app
from app.market_data.repository import store_historical_bars
from app.paper_worker.repository import store_preflight
from app.paper_worker.types import PaperWorkerPreflight, PaperWorkerPreflightOutcome


@pytest.fixture
def dashboard_db_session():
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_dashboard_returns_persisted_market_and_experiment_data(
    dashboard_db_session, monkeypatch
) -> None:
    store_historical_bars(dashboard_db_session, [_bar()])
    dashboard_db_session.commit()
    run = ExperimentRun(
        id="run-1",
        name="logistic_regression",
        model_version="baselines-v1",
        started_at=datetime(2026, 9, 22, tzinfo=UTC),
        accuracy=0.52,
        precision=0.54,
        roc_auc=0.505,
        registry_state=None,
    )
    monkeypatch.setattr("app.dashboard.service.load_experiment_runs", lambda *_: (run,))
    monkeypatch.setattr(dashboard_route, "load_experiment_runs", lambda *_: (run,))

    with _client(dashboard_db_session) as client:
        overview = client.get("/api/dashboard/overview")
        market = client.get("/api/dashboard/market?symbol=AAPL")
        models = client.get("/api/dashboard/models")

    assert overview.status_code == 200
    assert overview.json() == {
        "latest_market_bar_at": "2024-01-02T00:00:00Z",
        "market_bar_count": 1,
        "symbol_count": 1,
        "experiment_count": 1,
        "decision_count": 0,
        "positions_available": False,
        "strategy_results_available": False,
    }
    assert market.status_code == 200
    assert market.json()["candles"] == [
        {
            "timestamp": "2024-01-02T00:00:00Z",
            "open": "100.00000000",
            "high": "105.00000000",
            "low": "99.00000000",
            "close": "102.50000000",
            "volume": 1000,
        }
    ]
    assert models.status_code == 200
    assert models.json()["runs"][0]["name"] == "logistic_regression"
    assert models.json()["runs"][0]["roc_auc"] == 0.505


def test_dashboard_returns_empty_persisted_collections(dashboard_db_session, monkeypatch) -> None:
    monkeypatch.setattr("app.dashboard.service.load_experiment_runs", lambda *_: ())
    monkeypatch.setattr(dashboard_route, "load_experiment_runs", lambda *_: ())

    with _client(dashboard_db_session) as client:
        market = client.get("/api/dashboard/market?symbol=MSFT")
        models = client.get("/api/dashboard/models")
        trades = client.get("/api/dashboard/trades")

    assert market.status_code == 200
    assert market.json()["candles"] == []
    assert models.status_code == 200
    assert models.json() == {"runs": []}
    assert trades.status_code == 200
    assert trades.json() == {"decisions": []}


def test_dashboard_exposes_the_latest_worker_preflight(dashboard_db_session) -> None:
    from app.model_registry.service import ModelRegistryService
    from app.model_registry.types import ModelRegistration
    from app.risk.types import RiskLimits
    from app.strategy_deployments.service import StrategyDeploymentService
    from app.strategy_deployments.types import StrategyDeploymentSpec

    ModelRegistryService().register(
        dashboard_db_session,
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
    deployment = StrategyDeploymentService().create(
        dashboard_db_session,
        StrategyDeploymentSpec(
            name="Research deployment",
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
        ),
    )
    store_preflight(
        dashboard_db_session,
        PaperWorkerPreflight(
            deployment_id=deployment.id,
            outcome=PaperWorkerPreflightOutcome.BLOCKED,
            reason="model is not production",
            checked_at=datetime(2026, 9, 25, tzinfo=UTC),
        ),
    )
    dashboard_db_session.commit()

    with _client(dashboard_db_session) as client:
        response = client.get("/api/dashboard/deployments")

    assert response.status_code == 200
    assert response.json()["deployments"][0]["latest_preflight_outcome"] == "blocked"


def _client(db_session):
    app.dependency_overrides[get_db_session] = lambda: db_session
    return _DashboardClient()


class _DashboardClient:
    def __enter__(self) -> TestClient:
        self._client = TestClient(app)
        return self._client.__enter__()

    def __exit__(self, *_: object) -> None:
        self._client.__exit__(None, None, None)
        app.dependency_overrides.clear()


def _bar():
    from conftest import make_bar

    return make_bar()
