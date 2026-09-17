# ADR 021 — Evaluate Temporal Models with Symbol-Local Trailing Windows

## Status

Accepted

## Context

Phase 20 adds sequence models to feature rows whose target at timestamp `t` depends on
the next close. Building a global sequence can accidentally cross symbols, and fitting a
transformer or scaler on later observations can leak information into evaluation.

## Options Considered

### Flatten all symbols into one temporal sequence

This makes one large input array, but adjacent rows can describe different assets and do
not represent a meaningful market sequence.

### Fit sequence models on random splits

This is easy to implement but violates the chronological constraints already established
for predictive research.

### Build trailing per-symbol windows and reuse expanding walk-forward evaluation

This preserves asset identity, uses information available at each window end, and keeps
the existing timestamp gap and reserved later holdout.

## Decision

Use the versioned training dataset with its source symbol retained. Generate windows
within each independently timestamp-sorted symbol, ending at the feature row for the
existing next-day target. Apply the existing expanding walk-forward folds with their
mandatory gap, reserve the final fold for one holdout evaluation, and fit each fold's
scaler only on its training windows.

Evaluate fixed LSTM, GRU, temporal CNN, and Transformer classifier families through a
small CPU PyTorch adapter. Evaluate the existing random, majority-class, logistic
regression, and decision-tree controls on the newest observation of the exact same
windows and folds. Record settings and validation/holdout evidence in MLflow; do not
register, serve, or route those models into strategy, risk, or execution layers.

## Consequences

The sequence data contains fewer samples than the original row-level dataset because
each symbol needs a warm-up window. Training is slower than the tree and linear models,
and the fixed settings are research controls rather than optimized architecture claims.

The resulting leaderboard is a time-respecting predictive comparison. It remains
insufficient to select a production or paper-trading model, which is deferred to the
model-registry phase.
