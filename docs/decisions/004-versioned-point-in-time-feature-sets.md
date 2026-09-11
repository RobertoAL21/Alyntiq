# ADR 004 — Store Versioned Point-in-Time Feature Sets

## Status

Accepted

## Context

Feature calculations evolve as research improves. Replacing an already stored feature
value would make prior experiments irreproducible and could silently mix calculation
definitions. Features must also be demonstrably free of future-information leakage
before later phases consume them.

## Options Considered

### Recalculate features in memory for each consumer

This avoids another table but gives every consumer responsibility for using an identical
calculation version and source dataset. It also makes experiment lineage hard to audit.

### Store one mutable feature row per raw bar

This is simple initially, but a calculation change overwrites the historical inputs
used by earlier research.

### Store immutable, versioned feature rows

This preserves the input dataset for each calculation version and allows newer feature
definitions to coexist with earlier versions.

## Decision

Store calculated features in `market_features` under this unique identity:

```text
symbol + timestamp + source + timeframe + feature_version
```

The initial version is `features-v1`. A repeated build of the same version is
idempotent and does not overwrite stored rows. Feature calculations are exclusively
trailing or point-in-time, retain warm-up nulls, and have a leakage test that confirms
future raw bars cannot alter earlier results.

## Consequences

Research and later model phases can name both data provenance and the exact feature
definition they consume.

Changing a feature formula requires a new feature version and storage capacity for the
additional rows. This is an intentional reproducibility cost.

SPY and QQQ must be present in the selected market-bar dataset to produce market-context
features consistently.
