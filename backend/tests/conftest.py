from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models.market_bar import MarketBar  # noqa: F401
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
