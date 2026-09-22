# Frontend Dashboard

## Purpose

The frontend is a standalone React single-page application (SPA) that presents Alyntiq research and paper-trading information. It is located in `frontend/` and uses TypeScript, Vite, React Router, Tailwind CSS, and Lightweight Charts.

## Responsibilities

The frontend owns only presentation and user navigation:

- overview, positions, trades, strategies, models, and market views;
- table, badge, metric, and chart rendering;
- formatting values supplied by the backend.

It must not calculate predictions, derive trade proposals, approve risk, size positions, or submit broker orders. Those remain backend responsibilities.

## Current data boundary

Phase 27 replaces the demonstration fixture with typed, read-only API responses under
`/api/dashboard`. The browser accesses them through a same-origin `/api/` proxy: Vite
proxies to FastAPI in development, while the production Nginx image proxies to the Compose
`backend` service.

The available persisted sources are market bars in PostgreSQL, MLflow experiment runs,
model-registry records, and trading-audit decisions. The frontend shows an explicit empty
state when any of those sources has no records. It marks positions, portfolio performance,
strategy leaderboards, and point-in-time signals unavailable because the current
architecture does not persist authoritative records for them. It never polls the broker,
recreates a backtest, performs model inference, or submits an order.

## Running locally

```bash
cd frontend
npm install
npm run dev
```

The Vite development server listens on port `5173` by default.

## Verification

```bash
npm test
npm run build
```

When Compose is running, the browser can access the API at
`http://localhost:8080/api/dashboard/overview`.
