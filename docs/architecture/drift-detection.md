# Data and Model Drift

## Scope

Phase 23 adds a pure comparison service for detecting distributional changes between an
explicit historical reference sample and a later sample. It produces local structured
alerts for research or future operational consumers; it does not notify an external
system, retrain a model, alter a strategy, approve risk, or submit an order.

```text
versioned training inputs / model outputs / regime classifications
                              |
                              v
                  fixed reference sample
                              |
later completed observations -> DriftDetectionService -> DriftReport + alerts
```

## Comparison contract

The caller supplies the exact model-feature columns from a fixed training reference and
a later current window. The two frames must be non-empty, numeric, finite, and have the
same ordered columns. No feature is fetched, recomputed, or silently omitted by the
drift package. This retains the versioned feature and target boundaries established for
model research.

For every feature, and optionally for model predictions, the service calculates a
Population Stability Index (PSI). Quantile bins are learned from the reference sample
only, then used unchanged for the current sample. An alert is generated at or above the
configured feature or prediction PSI threshold (both default to `0.2`).

Volatility is an explicit optional pair of non-negative numeric samples, commonly a
trailing volatility feature. Its alert uses the absolute relative change between sample
means, with a default threshold of `0.3`. Regime monitoring accepts Phase 17 descriptive
market-regime classifications (or their `MarketRegime` labels) and alerts when the
deterministically selected dominant current regime differs from the dominant reference
regime. It never refits the regime detector.

## Alerts and boundaries

`DriftReport` retains all comparisons plus `DriftAlert` values for only breached
thresholds. Alerts are in-memory values returned to the caller, not broker actions,
webhooks, dashboard rules, or telemetry attributes. The report is evidence of a changed
input or output distribution, not proof of predictive degradation or a trading
instruction.

## CLI

From `backend/`, provide CSV samples and explicitly name the model feature contract:

```bash
python -m scripts.detect_drift \
  --reference-features training_features.csv \
  --current-features current_features.csv \
  --feature-columns returns_1d,momentum_5,volatility_20 \
  --reference-predictions training_predictions.csv \
  --current-predictions current_predictions.csv \
  --reference-volatility training_features.csv \
  --current-volatility current_features.csv \
  --volatility-column volatility_20 \
  --reference-regimes training_regimes.csv \
  --current-regimes current_regimes.csv
```

Prediction files use the `prediction` column by default; regime files use
`market_regime`. The command emits a JSON report, including every comparison and the
generated structured alerts. Thresholds and column names are configurable as command
arguments.

## Verification

From `backend/`, run:

```bash
ruff format --check .
ruff check .
pytest tests/test_drift_detection.py tests/test_detect_drift_cli.py
```
