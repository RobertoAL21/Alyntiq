# Target Generation

## Scope

Phase 4 defines the first supervised-learning label. It does not train a model,
produce predictions, select a strategy, or make trading decisions.

## Target Contract

`targets-v1` contains one binary classification target:

```text
direction_1d(t) = close(t + 1) > close(t)
```

The final bar of each symbol, source, and timeframe dataset has no known next-day
close, so its target is stored as null. A false value means that the next closing price
was equal to or below the current closing price.

## Flow

```text
market_bars (source + timeframe)
        ↓
TargetGenerator
        ↓
versioned target storage (market_targets)
```

## Isolation from Features

Targets intentionally use a future closing price to label historical observations.
They are therefore stored separately from `market_features` and are not returned by the
feature pipeline. A future model dataset must explicitly join features and targets on
their shared provenance-qualified bar identity; it must exclude null targets from
supervised training while retaining the latest feature row for inference.

## Stored Target Identity

Each `market_targets` row has immutable identity:

```text
symbol + timestamp + source + timeframe + target_version
```

The initial version is `targets-v1`. Re-running the same build uses `ON CONFLICT DO
NOTHING`, preserving published labels. Revised label definitions require a new target
version.

## CLI

From `backend/`, after applying migrations and ingesting historical bars:

```bash
python -m scripts.build_targets \
  --source alpaca:iex:raw \
  --timeframe 1D \
  --target-version targets-v1
```

The command prints received, inserted, and skipped counts, and fails when the selected
provenance has no stored bars.
