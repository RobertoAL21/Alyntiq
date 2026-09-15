# ADR 013: Bind paper execution to Alpaca's paper endpoint

## Status

Accepted

## Context

Phase 12 needs a broker contract for paper trading, while Alyntiq must never default to
real-money execution. The project already centralizes Alpaca credentials and uses explicit
risk decisions, but neither is sufficient if an execution adapter can be redirected to a
live broker endpoint.

## Decision

Define a provider-neutral `BrokerInterface` in `app.execution` and implement it with
`AlpacaPaperBroker`. Bind that adapter to Alpaca's official paper Trading API URL in code
and reject construction unless `TRADING_ENVIRONMENT=paper`.

The first order contract is intentionally narrow: whole-share market/day orders. A helper
can translate only an approved `RiskDecision` into that contract. The adapter is not wired
to FastAPI routes, strategies, workers, or scheduled jobs.

## Consequences

- A caller can inspect accounts, positions, and orders or explicitly submit/cancel a paper
  order through a stable interface.
- Production code cannot select Alpaca's live endpoint through configuration.
- The implementation remains testable with simulated HTTP responses and requires no broker
  SDK dependency.
- Future work must add order types, fill reconciliation, real-time updates, and any API or
  worker orchestration deliberately; they are not implied by this adapter.
