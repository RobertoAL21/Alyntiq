# Feature Engineering

## Scope

Phase 3 transforms validated, stored daily OHLCV bars into reproducible model inputs.
It implements feature calculation and versioned storage only. Model training,
backtesting, strategies, risk, execution, portfolio behavior, and frontend work remain
outside this domain.

## Flow

```text
market_bars (source + timeframe)
        ↓
FeatureEngineeringService
        ↓
point-in-time feature calculation
        ↓
market context join (SPY and QQQ)
        ↓
idempotent versioned storage (market_features)
```

## Feature Contract

`features-v1` contains return, momentum, moving-average, volatility, technical,
volume, and market-context values defined in
`app/features/constants.py`. Warm-up rows are retained with null values where their
trailing lookback window is incomplete. Downstream consumers must make their own
explicit completeness policy instead of silently dropping or filling those values.

All calculations use values at or before the current bar timestamp. Moving and rolling
windows are trailing; exponential windows use `adjust=False`. The feature calculator is
tested by modifying all future raw-bar values and confirming that earlier feature rows
are unchanged.

## Stored Feature Identity

Each `market_features` row has immutable identity:

```text
symbol + timestamp + source + timeframe + feature_version
```

`source` and `timeframe` carry forward the market-data provenance. `feature_version`
is part of the identity, allowing a revised calculation to be stored alongside an
existing feature set without overwriting it. Re-running a build for the same identity
uses `ON CONFLICT DO NOTHING`.

## CLI

From `backend/`, after applying migrations and ingesting the required symbols,
including `SPY` and `QQQ`:

```bash
python -m scripts.build_features \
  --source alpaca:iex:raw \
  --timeframe 1D \
  --feature-version features-v1
```

The command prints received, inserted, and skipped counts. It fails before storing if
the selected dataset lacks `SPY` or `QQQ`, because market-context features could not be
computed consistently.
