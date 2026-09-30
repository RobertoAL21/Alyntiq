# ADR 030 — Use JSON linear artifacts before runtime inference

## Context

The registry identifies reviewed model versions but existing research runs store metrics,
not a loadable predictor with its feature contract. Loading arbitrary Python pickles would
turn a database URI into code-execution authority and make model behavior opaque.

## Decision

Phase 30 introduces a narrow JSON artifact for standard-scaled binary logistic regression.
It stores scalar arrays, feature names, lineage, a training cutoff, and learned coefficients.
The runtime can validate and evaluate this representation without deserializing executable
objects. Training is explicit through a CLI and does not register or promote the result.

## Consequences

- Only linear logistic-regression models are supported by this phase.
- Existing MLflow experiment metrics cannot automatically become deployable artifacts.
- Future model families require their own reviewed, non-executable artifact contracts.
