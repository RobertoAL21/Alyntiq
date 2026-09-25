from collections.abc import Generator
from datetime import UTC, datetime

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models.market_bar import MarketBar  # noqa: F401
from app.db.models.market_feature import MarketFeature  # noqa: F401
from app.db.models.market_target import MarketTarget  # noqa: F401
from app.db.models.model_registry import ModelRegistryRecord  # noqa: F401
from app.db.models.paper_worker_preflight import PaperWorkerPreflightRecord  # noqa: F401
from app.db.models.strategy_deployment import StrategyDeploymentRecord  # noqa: F401
from app.db.models.trading_decision import TradingDecisionRecord  # noqa: F401
from app.market_data.schemas import HistoricalBar


def make_bar(
    timestamp: datetime = datetime(2024, 1, 2, tzinfo=UTC),
    symbol: str = "AAPL",
) -> HistoricalBar:
    return HistoricalBar(
        symbol=symbol,
        timestamp=timestamp,
        open="100.00",
        high="105.00",
        low="99.00",
        close="102.50",
        volume=1_000,
        source="alpaca:iex:raw",
        timeframe="1D",
    )


def make_feature_bars(periods: int = 80) -> pd.DataFrame:
    timestamps = pd.date_range("2024-01-02", periods=periods, freq="B", tz="UTC")
    rows = []
    for symbol, start, increment in (
        ("AAPL", 100.0, 1.0),
        ("SPY", 400.0, 0.5),
        ("QQQ", 350.0, 0.75),
    ):
        for index, timestamp in enumerate(timestamps):
            close = start + (increment * index)
            rows.append(
                {
                    "symbol": symbol,
                    "timestamp": timestamp,
                    "open": close - 0.25,
                    "high": close + 1.0,
                    "low": close - 1.0,
                    "close": close,
                    "volume": 1_000_000 + (index * 1_000),
                    "source": "alpaca:iex:raw",
                    "timeframe": "1D",
                }
            )
    return pd.DataFrame(rows)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    try:
        yield session
    finally:
        session.close()
        engine.dispose()
