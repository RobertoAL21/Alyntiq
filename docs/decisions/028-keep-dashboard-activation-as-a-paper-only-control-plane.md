# ADR 028 — Keep dashboard activation as a paper-only control plane

## Context

The read-only dashboard makes research results visible, but an operator needs a safe way to
prepare a reviewed configuration for a future paper-trading worker. Letting a browser start
an execution loop or call a broker would merge UI, model, strategy, risk, and execution
responsibilities and create an unsafe side-effect path.

## Options Considered

1. Add a dashboard button that starts a strategy worker and submits paper orders.
2. Keep all configuration in command-line arguments until a later worker exists.
3. Persist and validate a paper-strategy deployment, then stop at an explicit `armed` state.

## Decision

Choose option 3. Phase 28 adds only `draft`, `validated`, and `armed` deployment states.
The API validates registry provenance, paper environment, and fully explicit risk limits.
Mutating calls require an operator-controlled token supplied from configuration. The token is
a local deployment control, not a replacement for real authentication or authorization.

## Reasons

- It preserves the architecture: model → strategy → risk → execution.
- It gives the dashboard truthful operational state without inventing execution.
- It blocks accidental use of unreviewed models, mismatched feature/target lineage, and
  disabled risk limits.
- It gives a future worker a narrow, auditable input rather than browser-owned business logic.

## Consequences

- `armed` does not trade and must never be presented as a running strategy.
- Operators must set `DASHBOARD_CONTROL_TOKEN` to make changes; a missing token safely
  disables dashboard mutations.
- A future execution phase must introduce worker ownership, proper authentication,
  authorization, scheduling, audit events, and a separate transition to a running state.
