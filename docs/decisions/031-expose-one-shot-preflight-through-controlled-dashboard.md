# ADR 031 — Expose one-shot preflight through the controlled dashboard

## Context

The worker preflight is currently reachable only through a CLI, while the dashboard already
owns the token-gated deployment control plane. A fake Start/Stop switch would imply a
continuous runtime that does not exist and could mislead an operator about trading state.

## Decision

Expose one token-protected API endpoint that runs a single preflight cycle and returns its
persisted results. Add one compact dashboard control within the existing Models deployment
panel. The UI calls it a safety check, never a trading bot or execution action.

## Consequences

- Operators can trigger and inspect the real current runtime capability from the UI.
- The dashboard remains visually and architecturally small.
- A future continuous worker must introduce an actual lifecycle and then can receive truthful
  Start/Stop controls in a separate phase.
