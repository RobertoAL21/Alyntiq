from datetime import UTC, datetime

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
