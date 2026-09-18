# ADR 024 — Detect Drift Against Fixed Reference Samples

## Status

Accepted

## Context

Model inputs, prediction outputs, and market conditions can differ after a model's
training period. Alyntiq needs to expose those changes without mixing later observations
into the historical reference, treating a drift signal as trading advice, or coupling
the application to a notification vendor.

## Options Considered

### Compare each current window with itself

This can describe current variability but cannot identify deviation from the evidence on
which a model was trained.

### Refit reference distributions on every evaluation

This makes reported drift depend on later data and weakens reproducibility.

### Compare an explicit fixed reference with a later sample

This preserves a stable baseline and lets each signal be evaluated independently.

## Decision

Use a pure `DriftDetectionService` that receives complete reference and current samples.
It requires an exact feature-column contract, derives PSI bins solely from the reference
sample, and returns feature and optional prediction distribution comparisons. It reports
volatility as a relative change in sample means and reports a regime change when the
dominant descriptive current regime differs from the reference regime.

Threshold breaches return typed in-memory `DriftAlert` values. The service neither
persists, delivers, nor acts on alerts.

## Consequences

Callers must retain and provide the relevant training sample and feature contract, which
makes comparison provenance explicit. PSI and mean comparisons identify distributional
change, not model quality decline or a reason to trade. Alert delivery, model retraining,
dashboards, and automated policy responses remain separate future decisions.
