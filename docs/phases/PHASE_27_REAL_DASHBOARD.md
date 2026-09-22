# Phase 27 — Read-Only Research Dashboard

Status: COMPLETE

## Objective

Replace the frontend demonstration snapshot with read-only views of persisted research
data, without moving financial logic into React or creating an order-submission path.

## Scope

- read-only FastAPI dashboard endpoints for persisted market bars, MLflow experiment
  results, model-registry records, and trading-audit decisions;
- a same-origin frontend-to-backend proxy for the production Nginx image and a Vite proxy
  for local development;
- typed frontend data access, loading, error, and empty states;
- real market candles and model/trade tables where records exist; and
- explicit unavailable states for portfolio positions and historical strategy results,
  because those values are not persistently recorded by the current architecture.

## Out of Scope

- order submission, paper-broker polling, live trading, or broker credentials in the
  frontend;
- portfolio or strategy-result persistence, new financial calculations, or recomputing a
  backtest from a dashboard request;
- model inference, risk evaluation, or strategy execution from an HTTP route; and
- Grafana, Prometheus, authentication, or background workers.

## Definition of Done

- The dashboard no longer imports the hardcoded demonstration snapshot.
- Browser requests use typed, read-only API responses and never receive credentials.
- Data absence is represented explicitly rather than with synthetic values.
- Backend endpoint tests and frontend data-state tests cover success, empty, and failure
  behavior.
- Backend and frontend linting, tests, and production builds pass.

## Delivered

- read-only endpoints for overview facts, historical market bars, MLflow experiment runs,
  model-registry state, and trading-audit decisions;
- same-origin `/api/` proxying through Vite and the production Nginx frontend;
- typed frontend loading, failure, and empty states with the demonstration fixture removed;
- explicit unavailable views for unpersisted positions, strategy leaderboards, and model
  signals; and
- blank OTLP endpoint normalization, so the optional telemetry exporter remains disabled
  when no collector URL is configured.
