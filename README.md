# Alyntiq

Alyntiq is a professional AI-powered quantitative research and paper-trading platform. It is being built incrementally; this repository currently implements **Phase 0: Project Foundation** only.

The intended long-term flow is:

Market Data → Features → Models → Strategy → Risk → Execution → Portfolio

No market-data ingestion, ML, backtesting, strategy, execution, or trading functionality exists yet.

## Safety

Alyntiq is currently for research, backtesting, and paper trading only. `TRADING_ENVIRONMENT` defaults to `paper`; no real-money trading capability is implemented.

## Current architecture

The FastAPI application is in `backend/app`. The HTTP layer is isolated in `api/`, runtime settings and logging are in `core/`, and SQLAlchemy/Alembic infrastructure is in `db/` and `alembic/`. PostgreSQL and Redis are provisioned with Docker Compose for local development but are not yet used by business logic.

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

`ALPACA_API_KEY` and `ALPACA_SECRET_KEY` are intentionally optional in Phase 0. Do not commit `.env`.

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

## Run with Docker

After creating `.env`, build and start all services:

```bash
docker compose up --build
```

Docker uses `DOCKER_DATABASE_URL` when supplied, otherwise it points the backend at the Compose PostgreSQL service. Stop services with:

```bash
docker compose down
```

To apply the (currently empty) foundation migration in the backend container:

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
  alembic/             Database migration environment
  tests/               API tests
docker-compose.yml     Backend, PostgreSQL, and Redis services
```

GitHub Actions runs Ruff and pytest for pull requests and pushes to `main`.
