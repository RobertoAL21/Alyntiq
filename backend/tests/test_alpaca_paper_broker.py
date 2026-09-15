import json
from datetime import UTC, datetime
from decimal import Decimal
from urllib.parse import parse_qs, urlparse

import pytest

from app.backtesting.types import SignalSide
from app.core.config import Settings
from app.execution.alpaca import AlpacaPaperBroker, BrokerRequestError, PaperTradingSafetyError
from app.execution.service import broker_order_from_risk_decision
from app.execution.types import BrokerOrderRequest, BrokerOrderStatus, BrokerSide
from app.risk.types import ProposedOrder, RiskDecision, RiskRule


class FakeResponse:
    def __init__(self, payload: dict[str, object] | list[object] | None, status: int = 200) -> None:
        self._payload = payload
        self.status = status

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self) -> bytes:
        return b"" if self._payload is None else json.dumps(self._payload).encode()


def order_payload() -> dict[str, object]:
    return {
        "id": "order-123",
        "client_order_id": "alyntiq-order-1",
        "symbol": "AAPL",
        "side": "buy",
        "qty": "2",
        "filled_qty": "0",
        "status": "accepted",
        "submitted_at": "2024-01-02T15:30:00Z",
    }


def test_alpaca_paper_broker_uses_paper_endpoints_and_maps_responses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = iter(
        [
            FakeResponse(order_payload()),
            FakeResponse(
                {
                    "id": "account-123",
                    "cash": "1000",
                    "equity": "1250",
                    "buying_power": "2000",
                    "currency": "USD",
                }
            ),
            FakeResponse(
                [
                    {
                        "symbol": "AAPL",
                        "qty": "2",
                        "avg_entry_price": "100",
                        "market_value": "250",
                        "unrealized_pl": "50",
                    }
                ]
            ),
            FakeResponse([order_payload()]),
            FakeResponse(None, status=204),
        ]
    )
    requests = []

    def fake_urlopen(request, timeout: float):
        assert timeout == 30.0
        requests.append(request)
        return next(responses)

    monkeypatch.setattr("app.execution.alpaca.urlopen", fake_urlopen)
    broker = AlpacaPaperBroker(api_key="key", secret_key="secret")

    submitted = broker.submit_order(
        BrokerOrderRequest(
            symbol="aapl",
            side=BrokerSide.BUY,
            quantity=Decimal("2"),
            client_order_id="alyntiq-order-1",
        )
    )
    account = broker.get_account()
    positions = broker.get_positions()
    orders = broker.get_orders(BrokerOrderStatus.CLOSED, limit=50)
    broker.cancel_order("order-123")

    assert submitted.symbol == "AAPL"
    assert submitted.quantity == Decimal("2")
    assert account.equity == Decimal("1250")
    assert positions[0].unrealized_pnl == Decimal("50")
    assert orders[0].status == "accepted"
    assert all(
        request.full_url.startswith("https://paper-api.alpaca.markets/v2") for request in requests
    )
    assert requests[0].get_method() == "POST"
    assert json.loads(requests[0].data) == {
        "symbol": "AAPL",
        "qty": "2",
        "side": "buy",
        "type": "market",
        "time_in_force": "day",
        "client_order_id": "alyntiq-order-1",
    }
    assert requests[0].headers["Apca-api-key-id"] == "key"
    assert requests[4].get_method() == "DELETE"
    assert parse_qs(urlparse(requests[3].full_url).query) == {"status": ["closed"], "limit": ["50"]}


def test_paper_broker_blocks_live_settings_before_any_request() -> None:
    settings = Settings(
        trading_environment="live",
        alpaca_api_key="key",
        alpaca_secret_key="secret",
    )

    with pytest.raises(PaperTradingSafetyError, match="TRADING_ENVIRONMENT=paper"):
        AlpacaPaperBroker.from_settings(settings)


def test_paper_broker_requires_credentials_and_rejects_invalid_provider_responses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError, match="ALPACA_API_KEY"):
        AlpacaPaperBroker(api_key="", secret_key="")

    def fake_urlopen(request, timeout: float):
        return FakeResponse({})

    monkeypatch.setattr("app.execution.alpaca.urlopen", fake_urlopen)
    broker = AlpacaPaperBroker(api_key="key", secret_key="secret")

    with pytest.raises(BrokerRequestError, match="invalid id"):
        broker.submit_order(BrokerOrderRequest("AAPL", BrokerSide.BUY, Decimal("1")))


def test_execution_translates_only_an_approved_risk_decision() -> None:
    proposal = ProposedOrder(
        timestamp=datetime(2024, 1, 2, tzinfo=UTC),
        symbol="AAPL",
        side=SignalSide.BUY,
        quantity=2,
    )
    approved = RiskDecision(True, "approved", None, proposal, proposal)
    rejected = RiskDecision(False, "limit reached", RiskRule.MAXIMUM_DRAWDOWN, proposal, None)

    request = broker_order_from_risk_decision(approved, client_order_id="risk-approved-1")

    assert request.symbol == "AAPL"
    assert request.side is BrokerSide.BUY
    assert request.quantity == Decimal("2")
    assert request.client_order_id == "risk-approved-1"
    with pytest.raises(ValueError, match="approved risk decision"):
        broker_order_from_risk_decision(rejected)
