# ML Trading Strategy

## Scope

Phase 9 defines the strategy-side boundary between model probabilities and proposed
backtest actions. It does not train, persist, serve, or register a model. Those concerns
remain in the models domain and future model-registry work.

`ModelPrediction` is a point-in-time input with timestamp, symbol, upward probability,
model version, and feature version. `MLThresholdStrategy` accepts an indexed set of these
predictions, observes the matching completed bar, and emits one of:

```text
probability >= buy threshold  → BUY when no long position exists
probability <= sell threshold → SELL when a long position exists
otherwise                     → HOLD
```

`HOLD` is represented by no `Signal`. The strategy only proposes actions; the backtesting
engine still schedules an accepted signal for the next bar open. No risk decision, broker
order, paper-trading request, or model inference is performed by this phase.

## Validation-Only Threshold Selection

`select_thresholds` accepts `ValidationPrediction` values, the only input type that
contains a known label. It evaluates every supplied sell/buy threshold pair on that
validation collection and selects the pair with the highest directional accuracy across
all validation observations. Holds count as no correct directional action; ties prefer
greater action coverage and then a deterministic threshold order.

Operational `ModelPrediction` values contain no target. This type boundary prevents the
strategy from accessing labels during backtesting or inference and makes it explicit that
threshold selection must occur before holdout predictions are supplied to the strategy.

The initial candidate grid is 0.25–0.45 for sell and 0.55–0.75 for buy. These are
research inputs, not validated universal trading parameters. Any threshold-selection run
must record its validation period separately from its holdout evaluation.

## Version Lineage

Every model-driven signal carries `SignalLineage`:

- `model_version`
- `strategy_version`
- `feature_version`
- `up_probability`

The engine copies lineage through the order and fill. A closed trade retains both entry
and exit lineage, preserving the precise model/feature/strategy versions that produced
its decisions. Baseline strategy signals leave lineage empty.

## Manual Verification

The dedicated tests cover validation-only threshold selection, BUY/HOLD/SELL conversion,
next-open execution, and lineage on a closed trade:

```bash
cd backend
ruff format --check .
ruff check .
pytest tests/test_ml_strategy.py
```

This is historical-research infrastructure only. A probability threshold does not imply a
profitable strategy and is not financial advice.
