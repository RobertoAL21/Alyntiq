Phase 1 — Historical Market Data

Objective

Build a reliable historical market data pipeline.

Provider

Alpaca.

Architecture

Create a provider abstraction.

Example:

MarketDataProvider

Methods:

* get_historical_bars
* get_latest_quote

Implementation:

AlpacaMarketDataProvider

Initial Symbols

* AAPL
* MSFT
* NVDA
* SPY
* QQQ

Initial Timeframe

1D

Future:

* 1H
* 15m
* 5m

Data Model

MarketBar

Fields:

* id
* symbol
* timestamp
* open
* high
* low
* close
* volume
* source
* timeframe
* created_at

Unique constraint:

symbol + timestamp + timeframe + source

Requirements

Ingestion must be idempotent.

Do not insert duplicates.

Validation

Check:

* timestamps
* duplicate bars
* negative values
* OHLC consistency
* gaps

CLI

Example:

python -m scripts.ingest_market_data 
–symbol AAPL 
–start 2020-01-01 
–end 2026-01-01 
–timeframe 1D

Definition of Done

Historical bars can be fetched, validated and stored reproducibly.