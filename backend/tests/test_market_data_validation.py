from datetime import UTC, datetime

import pytest
from conftest import make_bar
from pydantic import ValidationError

from app.market_data.schemas import HistoricalBar
from app.market_data.validation import MarketDataValidationError, validate_historical_bars


def test_bar_rejects_invalid_ohlc_range() -> None:
    with pytest.raises(ValidationError, match="open must be between low and high"):
        HistoricalBar(
            symbol="AAPL",
            timestamp=datetime(2024, 1, 2, tzinfo=UTC),
            open="106.00",
            high="105.00",
            low="99.00",
            close="102.50",
            volume=1_000,
            source="alpaca:iex:raw",
            timeframe="1D",
        )


def test_batch_rejects_duplicate_timestamps() -> None:
    bar = make_bar()

    with pytest.raises(MarketDataValidationError, match="duplicate timestamp"):
        validate_historical_bars([bar, bar])


def test_batch_reports_potential_long_daily_gap() -> None:
    result = validate_historical_bars(
        [
            make_bar(datetime(2024, 1, 2, tzinfo=UTC)),
            make_bar(datetime(2024, 1, 8, tzinfo=UTC)),
        ]
    )

    assert len(result.potential_gaps) == 1
    assert result.potential_gaps[0].previous_timestamp == datetime(2024, 1, 2, tzinfo=UTC)
    assert result.potential_gaps[0].next_timestamp == datetime(2024, 1, 8, tzinfo=UTC)
