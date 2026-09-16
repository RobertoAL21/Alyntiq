# ADR 016: Keep the dashboard presentation-only until read APIs exist

## Context

Phase 15 introduces the standalone frontend dashboard, while the backend exposes only its health route and does not yet provide dashboard read models or endpoints.

## Decision

The initial SPA renders a typed, clearly labelled demonstration snapshot. It does not duplicate portfolio accounting, trading decisions, risk checks, or execution behavior in browser code. It also has no order-submission controls.

## Consequences

- The Phase 15 interface can establish navigation and visualization boundaries without claiming to show live or authoritative data.
- Future read-only FastAPI endpoints can replace the isolated fixture at a single data boundary.
- Backend domains remain the sole owners of financial and trading business logic.
