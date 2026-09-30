# Phase 30 — Reproducible Linear Model Artifacts

## Objective

Create a safe, transparent artifact format for a trained logistic-regression probability
model. The artifact must pin exact feature ordering, scaling values, learned coefficients,
training lineage, and a chronological training cutoff so later inference can be reproduced.

## Scope

Implement:

- a JSON-only, schema-validated artifact for binary logistic regression;
- deterministic artifact training from versioned feature/target rows before an explicit UTC
  training cutoff;
- exact feature-contract validation and in-process probability inference;
- a CLI to train and save the artifact; and
- tests and documentation describing registration as a separate review step.

## Explicitly Out of Scope

- automatic model selection, MLflow artifact replacement, or registry promotion;
- model serving, worker inference, persistent prediction records, or strategy signals;
- risk evaluation, account/portfolio access, broker polling, order submission, or live
  trading.

## Safety Invariants

1. The artifact contains data only; it never deserializes Python code or a pickle.
2. Its feature order must exactly match the inference feature contract.
3. Training excludes rows at or after the explicit cutoff and requires both target classes.
4. Creating an artifact does not register or promote it; a separate reviewed registry action
   remains required.
5. An artifact produces a probability only, not a trade action.
