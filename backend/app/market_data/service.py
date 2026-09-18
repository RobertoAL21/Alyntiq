import logging
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.market_data.providers import MarketDataProvider
from app.market_data.repository import StorageResult, store_historical_bars
from app.market_data.validation import ValidationResult, validate_historical_bars
from app.observability.telemetry import get_telemetry

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IngestionResult:
    storage: StorageResult
    validation: ValidationResult


class HistoricalMarketDataIngestionService:
    """Fetch, validate, and idempotently persist historical market-data bars."""

    def __init__(self, provider: MarketDataProvider) -> None:
        self._provider = provider

    def ingest(
        self,
        session: Session,
        symbol: str,
        start: date,
        end: date,
        timeframe: str = "1D",
    ) -> IngestionResult:
        try:
            bars = self._provider.get_historical_bars(symbol, start, end, timeframe)
            validation = validate_historical_bars(bars)
            storage = store_historical_bars(session, bars)
        except Exception:
            get_telemetry().record_ingestion_failure(source=type(self._provider).__name__)
            raise

        logger.info(
            "historical_market_data_ingested",
            extra={
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "received": storage.received,
                "inserted": storage.inserted,
                "skipped": storage.skipped,
                "potential_gaps": len(validation.potential_gaps),
            },
        )
        return IngestionResult(storage=storage, validation=validation)
