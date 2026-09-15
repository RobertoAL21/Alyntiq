# ADR 015: Use append-first trading-decision audit records

## Status

Accepted

## Context

Model lineage, strategy proposals, risk decisions, broker orders, and fills are separate
domain facts. Without a durable link, a later trade cannot reliably explain what was
predicted, proposed, approved, submitted, or executed. Updating a decision record freely
would allow later execution data to obscure the original rationale.

## Decision

Persist one UUID-keyed `TradingDecision` before broker submission. Store supplied model,
strategy, feature, prediction, confidence, signal, risk, quantity, and reason facts as
immutable decision data. Permit only monotonic lifecycle additions: an approved decision may
gain one order id and then one execution price/quantity.

Treat exact repeated order/execution reports as idempotent and reject conflicting updates.
Enforce the essential invariants both in domain values and the database schema.

## Consequences

- A decision can be reconstructed without making audit code own model, risk, or broker logic.
- Audit callers must write the record deliberately around any future execution workflow.
- Partial fills and later fill reconciliation require an explicit future audit model; this
  phase records one execution outcome per decision.
- Broker order ids are unique in the audit trail, preventing one provider order from being
  attributed to multiple decisions.
