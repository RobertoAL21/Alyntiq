# Alyntiq

Alyntiq is a professional AI-powered quantitative research and paper-trading platform.
Phases 0 through 28 are complete: foundation, historical market data, exploratory data
analysis, feature engineering, target generation, baseline-model evaluation, and
advanced-model evaluation, the historical backtesting engine, baseline strategies, the ML
threshold strategy, an independent pre-trade risk engine, multi-asset portfolio accounting,
and a paper-only Alpaca broker adapter, real-time Alpaca minute-bar consumption, a
trading-decision audit trail, isolated historical strategy competition, and descriptive
market-regime research, structured news research signals, hybrid strategy comparison, and
deep-learning time-series research, model lifecycle registry controls, OpenTelemetry
observability instrumentation, fixed-reference data and model drift detection,
production-oriented runtime images, CI validation and financial-safety gates, and the
final research report, the read-only research dashboard, and a paper-only strategy
deployment control plane.

The intended long-term flow is:

Market Data → Features → Models → Strategy → Risk → Execution → Portfolio

The roadmap is complete through the implemented phases. Read the evidence-focused [final research report](docs/research/final_results.md)
before interpreting this implementation as an investment system or a record of market
performance.

Historical market-data ingestion, versioned feature and target generation, walk-forward
model evaluation, a historical backtesting engine, comparable baseline strategies, and
versioned ML trading proposals, explicit historical risk decisions, and multi-asset
portfolio valuation, a tightly scoped paper-broker interface, ordered real-time bar
consumption, decision-to-execution audit records, isolated historical strategy
competition, descriptive market-regime research, structured news research signals, hybrid
strategy comparison, and reproducible deep-learning predictive comparison are available.
Model versions can now be registered with evaluation provenance and promoted through an
explicit lifecycle before model-driven paper orders. Live broker execution is not
implemented. OpenTelemetry records operational metrics and can export to an optional OTLP
collector; dashboards and alerting are not configured.

## Safety

Alyntiq is currently for research, backtesting, and paper trading only. `TRADING_ENVIRONMENT` defaults to `paper`; no real-money trading capability is implemented.

## Current architecture

The FastAPI application is in `backend/app`. The HTTP layer is isolated in `api/`,
runtime settings and JSON structured logging are in `core/`, SQLAlchemy/Alembic
infrastructure is in `db/`, historical market-data ingestion is in `market_data/`,
point-in-time transformations are in `features/`, labels are in `targets/`, and baseline,
advanced-model, and temporal deep-learning evaluation are in `models/`. The independent
`model_registry/` package owns model lifecycle records and paper-order eligibility.
The cross-cutting `observability/` package owns OpenTelemetry metrics and tracing setup.
The pure `drift/` package compares fixed historical references with later samples and
returns structured drift alerts without affecting trading decisions.
PostgreSQL, Redis, and a persistent
local MLflow store are provisioned with Docker Compose for local development. The pure,
in-memory historical simulator is isolated in `backtesting/`. Independent pre-trade risk
evaluation is isolated in `risk/`, multi-asset portfolio accounting is isolated in
`portfolio/`, the paper-only broker adapter is isolated in `execution/`, and real-time
market-data consumption is isolated in `market_data/`.
The immutable decision audit trail is isolated in `audit/`.
The standalone React dashboard is in `frontend/`.
The `strategy_deployments/` package owns persistent configuration states (`draft`,
`validated`, and `armed`) for a future paper worker; it does not execute trades.

## Frontend dashboard

The dashboard reads persisted market bars, MLflow experiment runs, model-registry records,
and trading-audit decisions through read-only FastAPI APIs. It clearly shows an empty or
unavailable state when data does not exist: portfolio positions, portfolio performance,
strategy-run results, and point-in-time signals are not persisted yet. It does not submit
orders or contain financial, risk, portfolio, strategy, or execution logic.

The Models page can also create, validate, arm, and disarm a paper-deployment configuration.
This is a control plane only: `armed` never starts a worker, loads a model, or contacts
Alpaca. Mutations require `DASHBOARD_CONTROL_TOKEN`, kept only in the page memory. To enable
the local controls, generate a separate value and place it in the untracked `.env`:

```bash
openssl rand -hex 32
# Copy the generated value into DASHBOARD_CONTROL_TOKEN in .env
```

The backend requires a `production` registry model with exactly matching feature and target
versions, `TRADING_ENVIRONMENT=paper`, and all risk limits explicitly configured before it
will arm a deployment. This local token is not public multi-user authentication.

```bash
cd frontend
npm install
npm run dev
```

## Requirements

- Python 3.12+
- Node.js 20+
- Docker and Docker Compose (for containerized development)

## Installation

Create and activate a virtual environment, then install the backend with development tools:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Configure environment variables from the repository root:

```bash
cp .env.example .env
```

`ALPACA_API_KEY` and `ALPACA_SECRET_KEY` are required for Alpaca ingestion, real-time data,
and the optional paper-broker adapter. Do not commit `.env`.

## Run locally

Start PostgreSQL and Redis first:

```bash
docker compose up -d postgres redis
cd backend
source .venv/bin/activate
alembic upgrade head
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`; browse the API docs at `http://localhost:8000/docs` or retrieve the schema at `http://localhost:8000/openapi.json`.

Verify the service:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok","service":"alyntiq-api"}
```

## Historical market-data ingestion

Phase 1 ingests validated, daily historical OHLCV bars from Alpaca. Set
`ALPACA_API_KEY` and `ALPACA_SECRET_KEY` in your untracked `.env`, then apply the
migration and run the CLI from `backend`:

```bash
alembic upgrade head
python -m scripts.ingest_market_data \
  --symbol AAPL \
  --start 2020-01-01 \
  --end 2026-01-01 \
  --timeframe 1D
```

The default feed is `iex`; set `ALPACA_DATA_FEED=sip` only when that feed is
available to the account. Stored bars record provider/feed/raw-data provenance and
are idempotent. Potential long gaps are reported for review rather than rejected,
because Phase 1 does not yet own an exchange calendar.

## Feature, target, and baseline evaluation

After ingesting the selected symbols, including `SPY` and `QQQ`, generate the versioned
feature and target sets from `backend`:

```bash
python -m scripts.build_features --source alpaca:iex:raw --timeframe 1D
python -m scripts.build_targets --source alpaca:iex:raw --timeframe 1D
```

Evaluate the required baseline classifiers with chronological expanding windows:

```bash
python -m scripts.run_baselines \
  --source alpaca:iex:raw \
  --timeframe 1D \
  --feature-version features-v1 \
  --target-version targets-v1 \
  --dataset-version dataset-v1 \
  --n-splits 3 \
  --gap 1
```

This command records the random, majority-class, logistic-regression, and decision-tree
results in local MLflow. Its predictive metrics are research outputs, not trading
performance or financial advice.

## Advanced-model evaluation

Phase 6 adds Random Forest, XGBoost, and LightGBM experiments. Optuna selects each
family's hyperparameters using the earlier expanding walk-forward folds, while the final
chronological fold remains an untouched holdout for the leaderboard:

```bash
python -m scripts.run_advanced_models \
  --source alpaca:iex:raw \
  --timeframe 1D \
  --feature-version features-v1 \
  --target-version targets-v1 \
  --dataset-version dataset-v1 \
  --n-splits 3 \
  --gap 1 \
  --n-trials 10
```

MLflow records the selected parameters, validation score, holdout metrics, trial history,
feature importance, and leaderboard. The output compares prediction quality only; it is
not a backtest, trading signal, or financial advice.

## Deep-learning time-series evaluation

Phase 20 adds fixed CPU PyTorch LSTM, GRU, temporal CNN, and Transformer classifiers.
Each model consumes symbol-local trailing windows of versioned features, uses the existing
expanding walk-forward evaluation with its next-day target gap, and is compared once on a
reserved final holdout with the existing random, majority-class, logistic-regression, and
decision-tree baselines.

```bash
python -m scripts.run_deep_learning_models \
  --source alpaca:iex:raw \
  --timeframe 1D \
  --feature-version features-v1 \
  --target-version targets-v1 \
  --dataset-version dataset-v1 \
  --n-splits 3 \
  --gap 1 \
  --lookback 20 \
  --epochs 10
```

MLflow records the temporal configuration, data lineage, validation evidence, untouched
holdout metrics, per-model artifacts, and leaderboard. The result is a predictive-research
comparison; it does not register, serve, or execute a model.

## Observability

Phase 22 instruments FastAPI and the existing model, risk, execution, market-data, and
backtest paths with OpenTelemetry. Set an OTLP/HTTP collector base URL when one is
available:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
OTEL_SERVICE_NAME=alyntiq-api
```

The application records API/model latency, prediction and trade volume, risk rejections,
ingestion failures, WebSocket reconnects, and backtest PnL/drawdown snapshots. Prometheus,
Grafana dashboards, alerting, and drift analysis are not configured in this phase.

## Historical backtesting engine

The Phase 7 engine supplies strategy-facing signals, orders, fills, long-only positions,
portfolio accounting, closed trades, an equity curve, and historical performance metrics.
A signal observed after a completed bar fills at the next bar's open, with configurable
commission and directional slippage. This prevents same-bar execution look-ahead.

The engine is intentionally single-symbol and long-only. It can apply optional, explicit
pre-trade risk decisions, but it has no broker integration, persistence, or paper/live
trading capability. See [the backtesting architecture](docs/architecture/backtesting.md)
for interfaces, metrics, assumptions, and verification commands.

## Baseline strategy comparison

Phase 8 adds Buy & Hold, Moving Average Crossover, RSI Mean Reversion, Momentum, and a
seeded Random strategy. All are run against the same source-qualified daily-bar period,
fixed quantity, and execution assumptions:

```bash
docker compose exec backend python -m scripts.run_baseline_strategies \
  --symbol AAPL \
  --start 2024-01-02 \
  --end 2024-12-31 \
  --quantity 100 \
  --commission-rate 0.001 \
  --slippage-bps 5
```

The command returns return, Sharpe, Sortino, maximum drawdown, and trade-count comparison
metrics. It is historical research only; it does not create a model-driven, risk-approved,
or broker-executable trade. See [the baseline strategy architecture](docs/architecture/baseline-strategies.md).

## ML threshold strategy

Phase 9 converts supplied, versioned model probabilities into BUY, SELL, or HOLD proposals.
Thresholds are selected only from labeled validation predictions; the strategy consumes
unlabeled point-in-time predictions and records model, feature, and strategy lineage on
the resulting closed trade. It does not train or serve a model, approve risk, or place an
order. See [the ML strategy architecture](docs/architecture/ml-strategy.md).

## Pre-trade risk engine

Phase 10 adds an optional independent risk stage between a strategy proposal and the
backtest's pending order. It can approve, reduce, or reject a proposed order using explicit
position-size, exposure, daily-realized-loss, drawdown, trade-count, and cash-reserve
limits. It also creates close-triggered stop-loss and take-profit exit proposals that fill
at the next bar open. Limits are disabled unless configured.

The engine is historical-research infrastructure only: it does not place broker orders,
mutate portfolio state, or enable paper/live execution. See [the risk-engine
architecture](docs/architecture/risk-engine.md) and [ADR 011](docs/decisions/011-use-explicit-pretrade-risk-decisions.md).

## Multi-asset portfolio engine

Phase 11 adds an immutable, long-only multi-asset portfolio ledger. It applies already
executed fills, tracks cash and open positions, allocates entry commissions across partial
sales, and marks all positions using explicit completed prices. Valuations report equity,
realized and unrealized PnL, and per-position and gross long exposure.

`FixedPercentageSizer` returns an incremental whole-share buy quantity for a target portion
of marked equity, capped by available cash. It neither creates orders nor replaces the
strategy, risk, or execution layers. The ledger remains independent from the paper-broker
adapter. See [the portfolio-engine architecture](docs/architecture/portfolio-engine.md) and
[ADR 012](docs/decisions/012-keep-multi-asset-portfolio-accounting-independent.md).

## Alpaca Paper Trading adapter

Phase 12 provides a provider-neutral broker interface plus `AlpacaPaperBroker` for account,
position, and order operations. It is hard-bound to Alpaca's paper endpoint and rejects any
setting other than `TRADING_ENVIRONMENT=paper`. It supports explicit whole-share market/day
orders only. The project-facing execution helper accepts an approved `RiskDecision` before
translating it to the broker contract.

There are no API routes, workers, scheduled tasks, or automatic order submission. Paper
orders remain simulated external side effects and are not a proxy for live performance. See
[the execution architecture](docs/architecture/execution-engine.md) and [ADR 013](docs/decisions/013-bind-paper-execution-to-alpaca-paper-endpoint.md).

## Real-time Alpaca minute bars

Phase 13 adds an asynchronous consumer for completed one-minute Alpaca stock bars. It uses
the configured IEX or SIP feed, authenticates with the existing Alpaca credentials, and
subscribes only to supplied symbols. It drops duplicate and out-of-order bars per symbol and
uses bounded exponential reconnects for connection failures and Alpaca's connection limit.

The consumer does not store bars or invoke feature, strategy, risk, execution, or broker
code. It starts no background task by itself. See [the real-time market-data
architecture](docs/architecture/realtime-market-data.md) and [ADR 014](docs/decisions/014-consume-ordered-minute-bars-from-alpaca-websockets.md).

## Trading audit trail

Phase 14 persists each `TradingDecision` with its model, strategy, and feature lineage;
prediction and confidence; signal; risk outcome; reason; broker order id; and execution
facts. An approved decision may gain one order id and one execution outcome. Exact repeated
reports are idempotent, while conflicting updates are rejected to preserve reconstruction.

The audit module records supplied facts only. It does not place an order or start an
automated execution workflow. Apply the migration with `alembic upgrade head`. See [the
trading-audit architecture](docs/architecture/trading-audit-trail.md) and [ADR 015](docs/decisions/015-use-append-first-trading-decision-audit-records.md).

## Run with Docker

After creating `.env` from `.env.example`, replace `POSTGRES_PASSWORD=replace-me` with a
local secret. Build and start the local integration environment:

```bash
docker compose up --build
```

Docker uses `DOCKER_DATABASE_URL` when supplied, otherwise it points the backend at the Compose PostgreSQL service. Stop services with:

```bash
docker compose down
```

To apply pending migrations in the backend container:

```bash
docker compose exec backend alembic upgrade head
```

The backend image runs as an unprivileged user and exposes `/health` on port `8000`; the
production SPA image uses Nginx on port `8080` and exposes its own static `/health` route.
See the [deployment architecture](docs/architecture/deployment.md) for image boundaries,
runtime configuration, migration handling, and the AWS reference topology.

## Quality checks

From `backend` with the virtual environment activated:

```bash
ruff check .
ruff format --check .
pytest
```

Optionally enable repository hooks from the repository root:

```bash
pre-commit install
```

## Project structure

```text
backend/
  app/                 FastAPI application
    api/routes/        HTTP endpoints
    core/              Settings and logging
    db/                SQLAlchemy engine, sessions, and base
    features/          Point-in-time feature pipeline
    targets/           Versioned supervised-learning targets
    models/            Dataset assembly, baseline, and advanced experiments
    backtesting/       Historical simulation and performance metrics
    risk/              Independent pre-trade risk decisions
    portfolio/         Multi-asset accounting and position sizing
    execution/         Paper-only broker contract and Alpaca adapter
    audit/             Immutable trading-decision audit records
    market_data/       Historical providers and real-time bar consumption
    strategies/        Baseline and ML trading-decision implementations
  alembic/             Database migration environment
  tests/               API tests
docker-compose.yml     Frontend, backend, PostgreSQL, and Redis services
frontend/Dockerfile     Production SPA image
```

GitHub Actions validates pull requests, `main` pushes, and manual runs with backend and
frontend quality checks, financial-safety checks, and Docker builds. It does not publish
images or deploy; see the [CI/CD architecture](docs/architecture/ci-cd.md).
