# Paper Execution and Broker Adapter

## Scope

Phase 12 introduces `app.execution`, a small execution boundary for Alpaca Paper Trading.
It exposes a provider-neutral `BrokerInterface` and an `AlpacaPaperBroker` implementation:

```text
Strategy proposal -> RiskDecision -> execution translation -> BrokerInterface -> Alpaca Paper API
```

The package does not train models, choose strategies, calculate risk limits, own portfolio
accounting, expose an HTTP endpoint, or run a background order loop.

## Paper-only safety boundary

`AlpacaPaperBroker` is permanently bound to
`https://paper-api.alpaca.markets/v2`; callers cannot configure a live trading endpoint.
`AlpacaPaperBroker.from_settings()` also rejects every environment except
`TRADING_ENVIRONMENT=paper` before a request can be made. Credentials continue to come only
from centralized `Settings` (`ALPACA_API_KEY` and `ALPACA_SECRET_KEY`).

The adapter uses the official Alpaca Paper Trading endpoints for account, positions, and
orders. Paper orders are still external side effects and simulated fills do not guarantee
live-market behavior. See Alpaca's [Trading API documentation](https://docs.alpaca.markets/us/docs/trading-api).

## Broker contract

`BrokerInterface` defines:

- `submit_order`;
- `cancel_order`;
- `get_account`;
- `get_positions`; and
- `get_orders`.

The first adapter intentionally supports whole-share, market, day orders only. It maps
provider responses to immutable account, position, and order values and raises a contextual
error for network, HTTP, or malformed-response failures without exposing credentials.

## Risk-to-execution handoff

`broker_order_from_risk_decision` converts only an approved `RiskDecision` with a modified
order into a `BrokerOrderRequest`. `submit_approved_order` invokes an injected broker with
that request. For a decision with model lineage, it additionally requires the Phase 21
model-registry gate and permits only a `production` model before contacting the broker.
This preserves the project-facing strategy -> risk -> execution path without allowing a
strategy, model, or registry to bypass independent risk approval. Neither function is
invoked by FastAPI or a background worker.

## Verification

From `backend/`, run:

```bash
ruff format --check .
ruff check .
pytest tests/test_alpaca_paper_broker.py
```
