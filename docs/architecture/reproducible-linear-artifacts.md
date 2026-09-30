# Reproducible Linear Artifacts

Phase 30 supplies a data-only artifact boundary between research datasets and future model
inference. A trainer consumes a versioned, fully labeled historical dataset before an
explicit cutoff and emits a JSON representation of a standard scaler plus binary logistic
regression coefficients.

```text
versioned features + targets -> explicit cutoff -> linear JSON artifact -> probability
```

The artifact is not a registry record, worker instruction, strategy signal, risk decision,
or broker request. Its exact feature-name order and lineage are checked before inference.
