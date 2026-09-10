# ADR 003 — Use Provider-Agnostic Historical Market Data with Stored Provenance

## Status

Accepted

## Context

Phase 1 needs reliable historical OHLCV data from Alpaca while preserving the option to
use another provider later. Data from different providers, feeds, or adjustment
policies must not be silently treated as identical records.

Historical market calendars contain valid non-trading periods. Treating every missing
calendar day as invalid would reject valid data without an exchange calendar.

## Options Considered

### Call Alpaca directly from ingestion code

This is initially concise but couples ingestion and future consumers to one provider's
response format and makes replacement difficult.

### Use a provider contract with provider-specific adapters

This separates normalized market-data records from the provider transport and response
format.

## Decision

Define a `MarketDataProvider` contract and implement it with
`AlpacaMarketDataProvider` in Phase 1.

Store bars under the unique identity:

```text
symbol + timestamp + timeframe + source
```

`source` records the provider, feed, and raw-data policy. The default source is
`alpaca:iex:raw`; the feed is configurable through centralized settings.

Validate timestamp, OHLC, volume, order, and duplicate invariants before storage.
Report potential long daily gaps for review, but do not reject them until Alyntiq owns
an exchange-calendar policy.

## Consequences

Provider-specific code remains isolated in the market-data adapter.

Repeated ingestion is idempotent through the database identity constraint and conflict
handling.

Consumers can distinguish data provenance rather than combining feeds or adjustment
policies accidentally.

Potential gaps require human review in Phase 1; calendar-aware classification is
deliberately deferred.
