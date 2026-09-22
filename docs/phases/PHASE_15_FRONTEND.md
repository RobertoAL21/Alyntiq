Phase 15 — Frontend Dashboard

Status: COMPLETE

Delivered:

* standalone React, TypeScript, Vite, React Router, Tailwind CSS, and Lightweight Charts application;
* overview, positions, trades, strategies, models, and market routes;
* presentation-only typed demonstration data, pending future backend read APIs;
* frontend linting, unit tests, and production build verification.

The demonstration-data boundary was replaced by the Phase 27 read-only research dashboard.

## Technology

- React

- TypeScript

- Vite

- React Router

- Tailwind CSS

- Lightweight Charts

## Architecture

The Alyntiq frontend will be a standalone React Single Page Application.

Responsibilities:

- React handles the user interface.

- React Router handles client-side routing.

- FastAPI exposes the backend REST API.

- WebSockets provide real-time updates when required.

- The frontend must not contain trading or financial business logic.

- Trading, risk, portfolio and ML logic must remain in the backend.

Next.js must not be introduced unless a future architectural decision explicitly changes the frontend architecture.

Pages

Overview

* portfolio value
* daily PnL
* total PnL
* cash
* exposure
* benchmark comparison

Positions

* symbol
* quantity
* average price
* current price
* PnL

Trades

* timestamp
* symbol
* action
* quantity
* price
* model
* confidence

Strategies

* strategy leaderboard
* Sharpe
* return
* drawdown

Models

* versions
* metrics
* training date

Market

* candlesticks
* volume
* indicators
* AI signals
