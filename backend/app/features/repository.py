from dataclasses import dataclass

import pandas as pd
from sqlalchemy import insert, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.db.models.market_bar import MarketBar
from app.db.models.market_feature import MarketFeature
from app.features.constants import FEATURE_COLUMNS

INSERT_BATCH_SIZE = 500


@dataclass(frozen=True)
class FeatureStorageResult:
    received: int
    inserted: int

    @property
    def skipped(self) -> int:
        return self.received - self.inserted


def load_market_bars(session: Session, source: str, timeframe: str) -> pd.DataFrame:
    """Load a single, provenance-qualified market-bar dataset for feature calculation."""
    statement = (
        select(
            MarketBar.symbol,
            MarketBar.timestamp,
            MarketBar.open,
            MarketBar.high,
            MarketBar.low,
            MarketBar.close,
            MarketBar.volume,
            MarketBar.source,
            MarketBar.timeframe,
        )
        .where(MarketBar.source == source, MarketBar.timeframe == timeframe)
        .order_by(MarketBar.symbol, MarketBar.timestamp)
    )
    return pd.read_sql(statement, session.connection())


def store_market_features(
    session: Session, features: pd.DataFrame, feature_version: str
) -> FeatureStorageResult:
    """Store versioned features idempotently without overwriting a published version."""
    if features.empty:
        return FeatureStorageResult(received=0, inserted=0)

    values = []
    for record in features.to_dict(orient="records"):
        values.append(
            {
                "symbol": record["symbol"],
                "timestamp": record["timestamp"],
                "source": record["source"],
                "timeframe": record["timeframe"],
                "feature_version": feature_version,
                **{
                    column: None if pd.isna(record[column]) else record[column]
                    for column in FEATURE_COLUMNS
                },
            }
        )

    inserted = 0
    for offset in range(0, len(values), INSERT_BATCH_SIZE):
        batch = values[offset : offset + INSERT_BATCH_SIZE]
        statement = _upsert_statement(session, batch)
        inserted += len(session.scalars(statement.returning(MarketFeature.id)).all())

    return FeatureStorageResult(received=len(values), inserted=inserted)


def _upsert_statement(session: Session, values: list[dict[str, object]]):
    dialect_name = session.get_bind().dialect.name
    if dialect_name == "postgresql":
        statement = postgresql_insert(MarketFeature).values(values)
    elif dialect_name == "sqlite":
        statement = sqlite_insert(MarketFeature).values(values)
    else:
        statement = insert(MarketFeature).values(values)

    return statement.on_conflict_do_nothing(
        index_elements=["symbol", "timestamp", "source", "timeframe", "feature_version"]
    )
