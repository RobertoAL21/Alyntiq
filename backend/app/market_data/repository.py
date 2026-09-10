from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import insert
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.db.models.market_bar import MarketBar
from app.market_data.schemas import HistoricalBar


@dataclass(frozen=True)
class StorageResult:
    received: int
    inserted: int

    @property
    def skipped(self) -> int:
        return self.received - self.inserted


def store_historical_bars(session: Session, bars: Sequence[HistoricalBar]) -> StorageResult:
    """Store bars once, based on their provider-qualified market-data identity."""
    if not bars:
        return StorageResult(received=0, inserted=0)

    values = [
        {
            "symbol": bar.symbol,
            "timestamp": bar.timestamp,
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "volume": bar.volume,
            "source": bar.source,
            "timeframe": bar.timeframe,
        }
        for bar in bars
    ]
    statement = _upsert_statement(session, values)
    inserted = len(session.scalars(statement.returning(MarketBar.id)).all())

    return StorageResult(received=len(bars), inserted=inserted)


def _upsert_statement(session: Session, values: list[dict[str, object]]):
    dialect_name = session.get_bind().dialect.name
    if dialect_name == "postgresql":
        statement = postgresql_insert(MarketBar).values(values)
    elif dialect_name == "sqlite":
        statement = sqlite_insert(MarketBar).values(values)
    else:
        statement = insert(MarketBar).values(values)

    return statement.on_conflict_do_nothing(
        index_elements=["symbol", "timestamp", "timeframe", "source"]
    )
