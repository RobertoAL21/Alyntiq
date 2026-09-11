# ADR 005 — Store Versioned Targets Separately from Features

## Status

Accepted

## Context

The initial prediction problem labels whether the next closing price exceeds the current
close. This definition necessarily uses future market information, while inference
features may only use information available at their timestamp. Storing labels with
features would make accidental target leakage easier and would make target-definition
changes difficult to reproduce.

## Options Considered

### Add target columns to `market_features`

This makes a later dataset join unnecessary, but mixes future-derived training labels
with point-in-time inference inputs.

### Recalculate labels in every model experiment

This avoids storage, but each experiment becomes responsible for reproducing the same
label definition and raw-data selection.

### Store a separate, versioned target dataset

This creates an explicit boundary between model inputs and supervised-learning labels
while preserving historical target definitions.

## Decision

Store `direction_1d` in `market_targets` with this identity:

```text
symbol + timestamp + source + timeframe + target_version
```

`targets-v1` defines `direction_1d(t)` as `close(t + 1) > close(t)`. The final bar of
each source-qualified symbol series stores a null label. Targets are never added to
`market_features`; future consumers must explicitly join the two datasets.

## Consequences

Model experiments can record and reproduce both a feature version and a target version.

Future target definitions require new versions and additional storage. Supervised
training must filter null labels, while inference can use the latest feature row without
a label.
