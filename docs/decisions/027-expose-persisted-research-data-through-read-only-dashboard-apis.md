# ADR 027 — Expose Persisted Research Data Through Read-Only Dashboard APIs

## Status

Accepted

## Context

The initial dashboard deliberately uses a presentation fixture because it has no backend
read APIs. PostgreSQL now stores market bars, model-registry records, and trading audit
records, while MLflow stores experiment results. React must not replicate financial or
trading logic, and the application has no persisted portfolio snapshot or strategy-run
history to truthfully display.

## Decision

Add a small read-only dashboard API that translates persisted records into presentation
schemas. The frontend fetches those schemas through a same-origin `/api/` proxy. It shows
real market bars, experiment records, registered models, and audit decisions; when a
domain has no persisted source, it renders an explicit empty or unavailable state.

The API does not initiate model inference, backtesting, risk evaluation, paper-broker
requests, or order submission. It does not create a persistence model merely to preserve
an ephemeral CLI result.

## Consequences

The dashboard becomes accurate about what is stored locally without exposing credentials
or moving business logic to the browser. Portfolio and strategy-result views remain
unavailable until their producing workflows persist authoritative snapshots under a
separate approved design.
