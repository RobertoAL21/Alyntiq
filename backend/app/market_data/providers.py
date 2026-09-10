from datetime import date
from typing import Protocol

from app.market_data.schemas import HistoricalBar, LatestQuote


class MarketDataProvider(Protocol):
    """Contract implemented by historical market-data providers."""

    def get_historical_bars(
        self,
        symbol: str,
        start: date,
        end: date,
        timeframe: str = "1D",
    ) -> list[HistoricalBar]:
        """Return historical OHLCV bars for an inclusive date range."""

    def get_latest_quote(self, symbol: str) -> LatestQuote:
        """Return the latest best bid and ask quote for one symbol."""
