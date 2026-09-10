import json
from datetime import date
from urllib.parse import parse_qs, urlparse

import pytest

from app.market_data.alpaca import AlpacaMarketDataProvider, AlpacaRequestError


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self, *_: object) -> bytes:
        return json.dumps(self._payload).encode()


def test_historical_bars_are_paginated_and_normalized(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = iter(
        [
            {
                "bars": [
                    {
                        "t": "2024-01-02T05:00:00Z",
                        "o": 100,
                        "h": 105,
                        "l": 99,
                        "c": 102.5,
                        "v": 1000,
                    }
                ],
                "next_page_token": "next-page",
            },
            {
                "bars": [
                    {
                        "t": "2024-01-03T05:00:00Z",
                        "o": 102.5,
                        "h": 106,
                        "l": 101,
                        "c": 104,
                        "v": 1200,
                    }
                ]
            },
        ]
    )
    requests: list[str] = []

    def fake_urlopen(request, timeout: float):
        assert timeout == 30.0
        requests.append(request.full_url)
        return FakeResponse(next(responses))

    monkeypatch.setattr("app.market_data.alpaca.urlopen", fake_urlopen)
    provider = AlpacaMarketDataProvider(api_key="key", secret_key="secret")

    bars = provider.get_historical_bars("aapl", date(2024, 1, 2), date(2024, 1, 3))

    assert [bar.symbol for bar in bars] == ["AAPL", "AAPL"]
    assert bars[0].source == "alpaca:iex:raw"
    assert parse_qs(urlparse(requests[1]).query)["page_token"] == ["next-page"]


def test_latest_quote_is_normalized(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(request, timeout: float):
        assert "quotes/latest" in request.full_url
        assert timeout == 30.0
        return FakeResponse(
            {
                "quote": {
                    "t": "2024-01-02T15:30:00Z",
                    "bp": 100.01,
                    "ap": 100.02,
                    "bs": 2,
                    "as": 3,
                }
            }
        )

    monkeypatch.setattr("app.market_data.alpaca.urlopen", fake_urlopen)
    provider = AlpacaMarketDataProvider(api_key="key", secret_key="secret")

    quote = provider.get_latest_quote("aapl")

    assert quote.symbol == "AAPL"
    assert str(quote.bid_price) == "100.01"
    assert quote.source == "alpaca:iex"


def test_provider_requires_credentials() -> None:
    with pytest.raises(ValueError, match="ALPACA_API_KEY"):
        AlpacaMarketDataProvider(api_key="", secret_key="")


def test_provider_wraps_invalid_bar_responses(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(request, timeout: float):
        return FakeResponse({"bars": [{"t": "2024-01-02T05:00:00Z"}]})

    monkeypatch.setattr("app.market_data.alpaca.urlopen", fake_urlopen)
    provider = AlpacaMarketDataProvider(api_key="key", secret_key="secret")

    with pytest.raises(AlpacaRequestError, match="invalid bar"):
        provider.get_historical_bars("AAPL", date(2024, 1, 2), date(2024, 1, 2))
