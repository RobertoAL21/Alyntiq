from dataclasses import dataclass

import pandas as pd
from sqlalchemy import insert, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.db.models.market_bar import MarketBar
from app.db.models.market_target import MarketTarget
from app.targets.constants import TARGET_COLUMNS, TARGET_IDENTITY_COLUMNS

INSERT_BATCH_SIZE = 1_000


@dataclass(frozen=True)
class TargetStorageResult:
    received: int
    inserted: int

    @property
    def skipped(self) -> int:
        return self.received - self.inserted


def load_market_bars(session: Session, source: str, timeframe: str) -> pd.DataFrame:
    """Load provenance-qualified closing prices for target generation."""
    statement = (
        select(
            MarketBar.symbol,
            MarketBar.timestamp,
            MarketBar.close,
            MarketBar.source,
            MarketBar.timeframe,
        )
        .where(MarketBar.source == source, MarketBar.timeframe == timeframe)
        .order_by(MarketBar.symbol, MarketBar.timestamp)
    )
    return pd.read_sql(statement, session.connection())


def store_market_targets(
    session: Session, targets: pd.DataFrame, target_version: str
) -> TargetStorageResult:
    """Store a versioned target set without overwriting published labels."""
    if targets.empty:
        return TargetStorageResult(received=0, inserted=0)

    values = [
        {
            **{column: record[column] for column in TARGET_IDENTITY_COLUMNS},
            "target_version": target_version,
            **{
                column: None if pd.isna(record[column]) else bool(record[column])
                for column in TARGET_COLUMNS
            },
        }
        for record in targets.to_dict(orient="records")
    ]

    inserted = 0
    for offset in range(0, len(values), INSERT_BATCH_SIZE):
        batch = values[offset : offset + INSERT_BATCH_SIZE]
        statement = _upsert_statement(session, batch)
        inserted += len(session.scalars(statement.returning(MarketTarget.id)).all())

    return TargetStorageResult(received=len(values), inserted=inserted)


def _upsert_statement(session: Session, values: list[dict[str, object]]):
    dialect_name = session.get_bind().dialect.name
    if dialect_name == "postgresql":
        statement = postgresql_insert(MarketTarget).values(values)
    elif dialect_name == "sqlite":
        statement = sqlite_insert(MarketTarget).values(values)
    else:
        statement = insert(MarketTarget).values(values)

    return statement.on_conflict_do_nothing(
        index_elements=["symbol", "timestamp", "source", "timeframe", "target_version"]
    )
