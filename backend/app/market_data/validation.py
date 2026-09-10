from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.market_data.schemas import HistoricalBar


class MarketDataValidationError(ValueError):
    """Raised when a batch of market bars violates ingestion invariants."""


@dataclass(frozen=True)
class MarketDataGap:
    """A potential daily-data gap that requires review, not automatic rejection."""

    previous_timestamp: datetime
    next_timestamp: datetime


@dataclass(frozen=True)
class ValidationResult:
    potential_gaps: tuple[MarketDataGap, ...]


def validate_historical_bars(bars: Sequence[HistoricalBar]) -> ValidationResult:
    """Validate batch-level ordering and identity while reporting unusual daily gaps.

    A market calendar is intentionally not inferred in Phase 1: exchange holidays,
    suspensions, and listing dates make a missing calendar day ambiguous. Gaps longer
    than four calendar days are therefore reported to callers rather than rejected.
    """

    errors: list[str] = []
    seen_timestamps: set[datetime] = set()
    potential_gaps: list[MarketDataGap] = []
    previous_bar: HistoricalBar | None = None

    for bar in bars:
        if bar.timestamp in seen_timestamps:
            errors.append(f"duplicate timestamp: {bar.timestamp.isoformat()}")
        seen_timestamps.add(bar.timestamp)

        if previous_bar is not None:
            if bar.timestamp < previous_bar.timestamp:
                errors.append("bars must be ordered by ascending timestamp")
            elif bar.timestamp - previous_bar.timestamp > timedelta(days=4):
                potential_gaps.append(
                    MarketDataGap(
                        previous_timestamp=previous_bar.timestamp,
                        next_timestamp=bar.timestamp,
                    )
                )
        previous_bar = bar

    if errors:
        raise MarketDataValidationError("; ".join(errors))

    return ValidationResult(potential_gaps=tuple(potential_gaps))
