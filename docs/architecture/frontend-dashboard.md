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

The backend currently has no read-only dashboard endpoints. The Phase 15 SPA therefore uses a clearly identified, typed demonstration snapshot in `src/data/dashboard-demo.ts`. It is an isolated presentation fixture, not a client-side trading implementation and not an authoritative portfolio record.

When a future phase adds read-only backend APIs, their response schemas should replace that fixture at the data boundary. The page and visualization components should remain presentation-only.

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
