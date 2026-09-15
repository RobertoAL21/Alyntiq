# Real-Time Market Data

## Scope

Phase 13 adds `AlpacaRealtimeBarStream` to `app.market_data`. It consumes completed
one-minute stock bars through Alpaca's WebSocket Market Data API and yields normalized,
immutable `RealtimeBar` values:

```text
Alpaca WebSocket -> real-time bar consumer -> future feature pipeline
```

The consumer does not persist data, calculate features, evaluate a strategy, call the risk
engine, or submit a broker order. Those actions remain distinct layers and are not started
by this module.

## Protocol and configuration

The stream URL is derived from the existing `ALPACA_DATA_FEED` setting:

```text
wss://stream.data.alpaca.markets/v2/{iex|sip}
```

It authenticates with the existing Alpaca API credentials using Alpaca's authentication
message, then subscribes only to the requested `bars` symbols. The official protocol sends
control and data messages in JSON arrays. See Alpaca's [streaming market-data
documentation](https://docs.alpaca.markets/us/docs/streaming-market-data).

## Event-quality policy

For each symbol, the consumer keeps the latest yielded bar timestamp. A bar with an equal
timestamp is a duplicate and is dropped; a bar with an earlier timestamp is out of order and
is also dropped. The implementation subscribes to completed `bars`, not `updatedBars`, so it
does not revise a bar after yielding it. Revised-bar handling and persistence need explicit
future policy.

## Failures and reconnects

The consumer treats WebSocket disconnections, operating-system connection errors, and
Alpaca error code `406` (connection limit) as transient. It reconnects with a bounded
exponential delay, defaulting to five retries from one second up to thirty seconds. Other
provider errors, including authentication failure, are surfaced without retrying.

The implementation creates one connection per stream invocation. Users must avoid opening
multiple consumers for the same Alpaca endpoint, because subscription tiers can limit the
number of simultaneous connections.

## Verification

From `backend/`, run:

```bash
ruff format --check .
ruff check .
pytest tests/test_realtime_market_data.py
```
