import json
from datetime import date
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.core.config import Settings
from app.market_data.schemas import HistoricalBar, LatestQuote


class AlpacaRequestError(RuntimeError):
    """Raised when Alpaca market-data requests cannot be completed safely."""


class AlpacaMarketDataProvider:
    """Alpaca REST implementation of the market-data provider contract."""

    source_name = "alpaca"

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        base_url: str = "https://data.alpaca.markets/v2",
        feed: str = "iex",
        timeout_seconds: float = 30.0,
    ) -> None:
        if not api_key or not secret_key:
            raise ValueError("ALPACA_API_KEY and ALPACA_SECRET_KEY must be configured")

        self._api_key = api_key
        self._secret_key = secret_key
        self._base_url = base_url.rstrip("/")
        self._feed = feed
        self._timeout_seconds = timeout_seconds

    @classmethod
    def from_settings(cls, settings: Settings) -> "AlpacaMarketDataProvider":
        return cls(
            api_key=settings.alpaca_api_key or "",
            secret_key=settings.alpaca_secret_key or "",
            base_url=settings.alpaca_data_url,
            feed=settings.alpaca_data_feed,
        )

    @property
    def source(self) -> str:
        """Identify the provider, feed, and unadjusted data policy in stored bars."""
        return f"{self.source_name}:{self._feed}:raw"

    def get_historical_bars(
        self,
        symbol: str,
        start: date,
        end: date,
        timeframe: str = "1D",
    ) -> list[HistoricalBar]:
        if timeframe != "1D":
            raise ValueError("Phase 1 supports only the 1D timeframe")
        if start > end:
            raise ValueError("start date must not be after end date")

        normalized_symbol = symbol.strip().upper()
        if not normalized_symbol:
            raise ValueError("symbol must not be blank")

        parameters: dict[str, str] = {
            "timeframe": timeframe,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "feed": self._feed,
            "limit": "10000",
            "sort": "asc",
        }
        bars: list[HistoricalBar] = []

        while True:
            payload = self._get_json(f"/stocks/{normalized_symbol}/bars", parameters)
            raw_bars = payload.get("bars", [])
            if not isinstance(raw_bars, list):
                raise AlpacaRequestError("Alpaca returned an invalid bars response")

            try:
                bars.extend(
                    HistoricalBar(
                        symbol=normalized_symbol,
                        timestamp=raw_bar["t"],
                        open=raw_bar["o"],
                        high=raw_bar["h"],
                        low=raw_bar["l"],
                        close=raw_bar["c"],
                        volume=raw_bar["v"],
                        source=self.source,
                        timeframe=timeframe,
                    )
                    for raw_bar in raw_bars
                )
            except (KeyError, TypeError, ValueError) as error:
                raise AlpacaRequestError("Alpaca returned an invalid bar") from error

            next_page_token = payload.get("next_page_token")
            if not next_page_token:
                return bars
            if not isinstance(next_page_token, str):
                raise AlpacaRequestError("Alpaca returned an invalid pagination token")
            parameters["page_token"] = next_page_token

    def get_latest_quote(self, symbol: str) -> LatestQuote:
        normalized_symbol = symbol.strip().upper()
        if not normalized_symbol:
            raise ValueError("symbol must not be blank")

        payload = self._get_json(f"/stocks/{normalized_symbol}/quotes/latest", {"feed": self._feed})
        raw_quote = payload.get("quote")
        if not isinstance(raw_quote, dict):
            raise AlpacaRequestError("Alpaca returned an invalid latest quote response")

        try:
            return LatestQuote(
                symbol=normalized_symbol,
                timestamp=raw_quote["t"],
                bid_price=raw_quote["bp"],
                ask_price=raw_quote["ap"],
                bid_size=raw_quote["bs"],
                ask_size=raw_quote["as"],
                source=f"{self.source_name}:{self._feed}",
            )
        except (KeyError, TypeError, ValueError) as error:
            raise AlpacaRequestError("Alpaca returned an invalid latest quote") from error

    def _get_json(self, path: str, parameters: dict[str, str]) -> dict[str, Any]:
        query = urlencode(parameters)
        request = Request(
            f"{self._base_url}{path}?{query}",
            headers={
                "APCA-API-KEY-ID": self._api_key,
                "APCA-API-SECRET-KEY": self._secret_key,
                "Accept": "application/json",
            },
        )

        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:  # noqa: S310
                payload = json.load(response)
        except HTTPError as error:
            raise AlpacaRequestError(f"Alpaca request failed with status {error.code}") from error
        except URLError as error:
            raise AlpacaRequestError("Alpaca request could not be reached") from error
        except json.JSONDecodeError as error:
            raise AlpacaRequestError("Alpaca returned invalid JSON") from error

        if not isinstance(payload, dict):
            raise AlpacaRequestError("Alpaca returned an invalid response")
        return payload
