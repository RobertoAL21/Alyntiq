from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes import strategy_deployments as deployment_route
from app.core.config import Settings
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app
from app.model_registry.service import ModelRegistryService
from app.model_registry.types import ModelRegistration, ModelState


@pytest.fixture
def deployment_db_session():
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


def test_control_api_requires_configured_token_and_never_arms_unreviewed_models(
    deployment_db_session, monkeypatch
) -> None:
    monkeypatch.setattr(
        deployment_route,
        "get_settings",
        lambda: Settings(_env_file=None, DASHBOARD_CONTROL_TOKEN="local-control"),
    )
    ModelRegistryService().register(
        deployment_db_session,
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
    deployment_db_session.commit()
    with _client(deployment_db_session) as client:
        denied = client.post("/api/control/strategy-deployments", json=_payload())
        created = client.post(
            "/api/control/strategy-deployments",
            json=_payload(),
            headers={"X-Alyntiq-Control-Token": "local-control"},
        )
        validation = client.post(
            f"/api/control/strategy-deployments/{created.json()['id']}/validate",
            headers={"X-Alyntiq-Control-Token": "local-control"},
        )

    assert denied.status_code == 401
    assert created.status_code == 201
    assert validation.status_code == 422
    assert "not production" in validation.json()["detail"]


def test_control_api_creates_validates_arms_and_exposes_read_only_status(
    deployment_db_session, monkeypatch
) -> None:
    _register_production_model(deployment_db_session)
    monkeypatch.setattr(
        deployment_route,
        "get_settings",
        lambda: Settings(_env_file=None, DASHBOARD_CONTROL_TOKEN="local-control"),
    )
    with _client(deployment_db_session) as client:
        created = client.post(
            "/api/control/strategy-deployments",
            json=_payload(),
            headers={"X-Alyntiq-Control-Token": "local-control"},
        )
        deployment_id = created.json()["id"]
        validated = client.post(
            f"/api/control/strategy-deployments/{deployment_id}/validate",
            headers={"X-Alyntiq-Control-Token": "local-control"},
        )
        armed = client.post(
            f"/api/control/strategy-deployments/{deployment_id}/arm",
            headers={"X-Alyntiq-Control-Token": "local-control"},
        )
        status = client.get("/api/dashboard/deployments")
        disarmed = client.post(
            f"/api/control/strategy-deployments/{deployment_id}/disarm",
            headers={"X-Alyntiq-Control-Token": "local-control"},
        )

    assert created.status_code == 201
    assert created.json()["state"] == "draft"
    assert validated.json()["state"] == "validated"
    assert armed.json()["state"] == "armed"
    assert status.json()["deployments"][0]["state"] == "armed"
    assert disarmed.json()["state"] == "validated"


def test_control_api_is_disabled_without_a_configured_token(
    deployment_db_session, monkeypatch
) -> None:
    monkeypatch.setattr(deployment_route, "get_settings", lambda: Settings(_env_file=None))

    with _client(deployment_db_session) as client:
        response = client.post("/api/control/strategy-deployments", json=_payload())

    assert response.status_code == 503


def _client(db_session):
    app.dependency_overrides[get_db_session] = lambda: db_session
    return _DeploymentClient()


class _DeploymentClient:
    def __enter__(self) -> TestClient:
        self._client = TestClient(app)
        return self._client.__enter__()

    def __exit__(self, *_: object) -> None:
        self._client.__exit__(None, None, None)
        app.dependency_overrides.clear()


def _register_production_model(session) -> None:
    registry = ModelRegistryService()
    registry.register(
        session,
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
        session,
        model_version="reviewed-v1",
        target_state=ModelState.STAGING,
        now=datetime(2026, 9, 24, tzinfo=UTC),
    )
    registry.transition(
        session,
        model_version="reviewed-v1",
        target_state=ModelState.PRODUCTION,
        now=datetime(2026, 9, 24, 1, tzinfo=UTC),
    )
    session.commit()


def _payload() -> dict[str, object]:
    return {
        "name": "Reviewed daily momentum",
        "model_version": "reviewed-v1",
        "strategy_version": "ml-strategy-v1",
        "feature_version": "features-v1",
        "target_version": "targets-v1",
        "source": "alpaca:iex:raw",
        "timeframe": "1D",
        "symbols": ["AAPL", "MSFT"],
        "buy_threshold": "0.60",
        "sell_threshold": "0.40",
        "order_quantity": 10,
        "risk_limits": {
            "maximum_position_size_pct": "0.10",
            "maximum_portfolio_exposure": "0.40",
            "maximum_daily_loss_pct": "0.03",
            "maximum_drawdown_pct": "0.10",
            "stop_loss_pct": "0.04",
            "take_profit_pct": "0.08",
            "max_trades_per_day": 4,
            "minimum_cash_reserve": "1000",
        },
    }
