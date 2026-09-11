# Alyntiq

Alyntiq is a professional AI-powered quantitative research and paper-trading platform.
Phases 0 through 5 are complete: foundation, historical market data, exploratory data
analysis, feature engineering, target generation, and baseline-model evaluation.

The intended long-term flow is:

Market Data → Features → Models → Strategy → Risk → Execution → Portfolio

Historical market-data ingestion, versioned feature and target generation, and
walk-forward baseline-model evaluation are available. Backtesting, strategies, risk,
execution, and trading functionality are not implemented.

## Safety

Alyntiq is currently for research, backtesting, and paper trading only. `TRADING_ENVIRONMENT` defaults to `paper`; no real-money trading capability is implemented.

## Current architecture

The FastAPI application is in `backend/app`. The HTTP layer is isolated in `api/`,
runtime settings and JSON structured logging are in `core/`, SQLAlchemy/Alembic
infrastructure is in `db/`, historical market-data ingestion is in `market_data/`,
point-in-time transformations are in `features/`, labels are in `targets/`, and baseline
evaluation is in `models/`. PostgreSQL, Redis, and a persistent local MLflow store are
provisioned with Docker Compose for local development.

## Requirements

- Python 3.12+
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

`ALPACA_API_KEY` and `ALPACA_SECRET_KEY` are required only for Alpaca ingestion. Do not
commit `.env`.

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

## Run with Docker

After creating `.env`, build and start all services:

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
    models/            Dataset assembly and baseline experiments
  alembic/             Database migration environment
  tests/               API tests
docker-compose.yml     Backend, PostgreSQL, and Redis services
```

GitHub Actions runs Ruff and pytest for pull requests and pushes to `main`.
