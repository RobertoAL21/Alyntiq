from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.backtesting.types import BacktestBar
from app.db.models.market_bar import MarketBar


class BacktestDataError(ValueError):
    """Raised when selected stored market data cannot produce a historical backtest."""


@dataclass(frozen=True)
class BacktestDataset:
    symbol: str
    source: str
    timeframe: str
    start: date
    end: date
    bars: tuple[BacktestBar, ...]


def load_backtest_dataset(
    session: Session,
    *,
    symbol: str,
    source: str,
    timeframe: str,
    start: date,
    end: date,
) -> BacktestDataset:
    """Load one provenance-qualified daily series into the engine's neutral bar contract."""
    if start > end:
        raise BacktestDataError("start date must not be after end date")
    normalized_symbol = symbol.strip().upper()
    if not normalized_symbol:
        raise BacktestDataError("symbol must not be blank")
    start_timestamp = datetime.combine(start, time.min, tzinfo=UTC)
    end_exclusive = datetime.combine(end + timedelta(days=1), time.min, tzinfo=UTC)
    statement = (
        select(MarketBar)
        .where(
            MarketBar.symbol == normalized_symbol,
            MarketBar.source == source,
            MarketBar.timeframe == timeframe,
            MarketBar.timestamp >= start_timestamp,
            MarketBar.timestamp < end_exclusive,
        )
        .order_by(MarketBar.timestamp)
    )
    bars = tuple(
        BacktestBar(
            timestamp=_as_utc(row.timestamp),
            symbol=row.symbol,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
        )
        for row in session.scalars(statement)
    )
    if not bars:
        raise BacktestDataError("no stored market bars match the requested backtest dataset")
    return BacktestDataset(
        symbol=normalized_symbol,
        source=source,
        timeframe=timeframe,
        start=start,
        end=end,
        bars=bars,
    )


def _as_utc(timestamp: datetime) -> datetime:
    """Normalize SQLite's timezone-less round trip while preserving UTC market-bar semantics."""
    return timestamp.replace(tzinfo=UTC) if timestamp.tzinfo is None else timestamp.astimezone(UTC)
