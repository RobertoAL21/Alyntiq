# ADR 010 — Separate Validation Threshold Selection from ML Signal Generation

## Status

Accepted

## Context

An ML probability is a prediction, not a trading decision. Converting it to BUY, SELL, or
HOLD requires thresholds. Selecting those thresholds on the same holdout period used to
report trading performance would overfit the strategy to its evaluation result.

Phase 6 tracks model experiments but deliberately does not create a model registry or an
inference service. Phase 9 must therefore consume versioned point-in-time predictions
without introducing those later capabilities.

## Options Considered

### Embed thresholds in a model or optimize them on the holdout period

This conflates the model and strategy layers and produces an optimistic holdout result.

### Let the strategy access labels while it runs

This introduces direct future information into a trading decision.

### Select thresholds from labeled validation predictions, then consume unlabeled predictions

This keeps threshold fitting chronological and preserves a clear model-to-strategy
boundary.

## Decision

Use two separate inputs:

- `ValidationPrediction` contains a prediction and known target solely for
  validation-time threshold selection.
- `ModelPrediction` contains no target and is the only prediction input accepted by
  `MLThresholdStrategy`.

The strategy maps probabilities to BUY, SELL, or HOLD using already selected thresholds.
Its model, strategy, and feature versions travel with the generated signal through order,
fill, position, and closed-trade lineage. The strategy does not perform risk approval or
broker execution.

## Consequences

Threshold selection is reproducible and cannot read labels during strategy execution.
Callers must retain the validation/holdout split provenance around a strategy experiment.
Producing persisted model predictions, choosing risk-approved quantity, and placing a
paper order remain separate future responsibilities.
