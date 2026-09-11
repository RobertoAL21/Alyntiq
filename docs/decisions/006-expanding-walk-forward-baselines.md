# ADR 006 — Evaluate Baselines with Expanding Walk-Forward Windows

## Status

Accepted

## Context

Market observations are time ordered. Randomly mixing observations between training and
evaluation would let a model learn from a future period and measure performance on an
earlier period. The one-day target also means a label at timestamp `t` requires a close
from `t + 1`.

## Options Considered

### Random train/test split

This is straightforward, but violates chronological evaluation and produces overly
optimistic estimates for autocorrelated market data.

### One fixed chronological split

This preserves time order, but evaluates only one historical boundary and provides less
evidence about baseline stability.

### Expanding walk-forward windows with a one-timestamp gap

This repeatedly trains on earlier data, evaluates on later data, and excludes the label
boundary from the training window.

## Decision

Phase 5 uses timestamp-aligned expanding walk-forward folds. Training windows expand
across folds; every test window is strictly later; and a mandatory one-timestamp gap
separates them for the next-day target horizon. Features and targets remain separate
until the explicit training-dataset join.

The required models are random prediction, majority class, logistic regression, and a
decision tree. All runs record version lineage and metrics in MLflow.

## Consequences

Evaluation is slower than a random split and produces folds with different training
sizes, but it provides a time-respecting baseline for later model phases.

The current splitter assumes timestamps represent a common daily cadence. Handling
exchange calendars and multi-horizon target gaps requires an explicit future decision.
