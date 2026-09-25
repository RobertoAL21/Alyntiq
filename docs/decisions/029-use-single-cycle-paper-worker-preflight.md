# ADR 029 — Use a single-cycle paper-worker preflight before execution

## Context

An armed deployment is reviewed configuration, not proof that it remains eligible later.
Model lifecycle state or runtime environment can change after it is armed. Alyntiq currently
has no reproducible artifact loader, authoritative live portfolio snapshot, or fill
reconciliation loop, so a worker that submits broker orders would be unsafe and incomplete.

## Options Considered

1. Start a continuous worker that loads models and submits paper orders now.
2. Keep the deployment state static until every runtime dependency exists.
3. Add a durable, single-cycle preflight that rechecks an armed deployment and records its
   result before any execution phase.

## Decision

Choose option 3. The Phase 29 CLI runs one preflight cycle only. It reuses deployment
eligibility checks, persists `ready` or `blocked` outcomes, and has no dependency on model,
strategy, risk, execution, broker, or portfolio packages.

## Consequences

- Operators get current, auditable evidence that an armed configuration is still eligible.
- The command cannot trade, even against the paper broker.
- A later execution phase must deliberately add artifact loading, point-in-time inference,
  strategy/risk handoff, portfolio reconciliation, idempotency, and broker side effects.
