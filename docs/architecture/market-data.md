# Historical Market Data

## Scope

Phase 1 implements daily historical OHLCV ingestion for US equities and ETFs from
Alpaca. It does not implement real-time data, feature engineering, strategies, risk,
execution, or portfolio behavior.

## Flow

```text
AlpacaMarketDataProvider
        ↓
HistoricalMarketDataIngestionService
        ↓
batch validation
        ↓
idempotent PostgreSQL storage (market_bars)
```

`MarketDataProvider` is the provider-neutral interface. `AlpacaMarketDataProvider`
uses Alpaca's historical stock-bars and latest-quote endpoints. Provider credentials
and the selected data feed are read only from centralized settings.

## Stored Bar Identity

Each `market_bars` row has the following immutable data identity:

```text
symbol + timestamp + timeframe + source
```

`source` records the provider, selected feed, and raw-data policy; the default is
`alpaca:iex:raw`. Re-running an identical ingestion uses `ON CONFLICT DO NOTHING`,
so no duplicate bars are stored.

## Validation

Each bar must have a timezone-aware timestamp, positive OHLC prices, non-negative
volume, and OHLC values consistent with its low/high range. A batch must be ordered
and contain no duplicate timestamps.

Daily gaps longer than four calendar days are reported in the ingestion result and
structured logs. They are not rejected automatically: holidays, suspensions, IPO
dates, and symbol history require an exchange calendar before a missing day can be
classified as invalid.

## CLI

From `backend/`, after applying migrations and configuring `ALPACA_API_KEY` and
`ALPACA_SECRET_KEY` in the repository `.env` file:

```bash
python -m scripts.ingest_market_data \
  --symbol AAPL \
  --start 2020-01-01 \
  --end 2026-01-01 \
  --timeframe 1D
```

The CLI prints received/inserted/skipped counts and potential-gap count. Phase 1
accepts only `1D` bars.
