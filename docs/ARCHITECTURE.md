Alyntiq — Architecture

High-Level Architecture

Alyntiq follows a modular pipeline architecture.

Market Data Provider
↓
Market Data Ingestion
↓
Market Data Storage
↓
Feature Pipeline
↓
Model Inference
↓
Strategy Engine
↓
Risk Engine
↓
Execution Engine
↓
Broker
↓
Portfolio Engine
↓
Analytics

Additional systems include:

* experiment tracking
* model registry
* audit trail
* observability
* frontend
* background workers

Main Domains

Market Data

Responsible for:

* historical OHLCV data
* latest quotes
* real-time market events
* provider abstractions
* data validation
* ingestion

Features

Responsible for transforming historical information into model inputs.

Features must never contain future information.

Models

Responsible only for predictions.

Example:

P(price increases over next period) = 0.72

A model must not directly decide position size or execute an order.

Strategies

Responsible for interpreting predictions and market conditions.

Example:

If prediction > threshold and market regime is acceptable, propose BUY.

Risk

Responsible for determining whether a proposed trade is acceptable.

Examples:

* position size limits
* portfolio exposure
* drawdown limits
* stop losses
* daily loss limits

Execution

Responsible for converting approved actions into broker orders.

Broker

Provides an abstraction around order execution.

Initial broker:

Alpaca Paper Trading.

Portfolio

Responsible for:

* cash
* positions
* equity
* realized PnL
* unrealized PnL
* exposure

Architectural Rule

Each domain must communicate through explicit interfaces or schemas.

Avoid circular dependencies between domains.

Initial Repository Architecture

backend/
app/
api/
core/
db/
market_data/
features/
models/
strategies/
risk/
execution/
portfolio/
backtesting/
services/
workers/

frontend/

data/

models/

scripts/

docs/

notebooks/

Research vs Production Code

Notebooks may be used for:

* exploration
* visualization
* experimentation
* hypothesis testing

Production logic must not exist only inside notebooks.

Reusable logic must be moved into application modules.