Phase 0 — Project Foundation

Objective

Create the engineering foundation for Alyntiq.

Technologies

* Python 3.12+
* FastAPI
* Uvicorn
* Pydantic
* Pydantic Settings
* SQLAlchemy
* Alembic
* PostgreSQL
* Redis
* Docker
* Docker Compose
* pytest
* Ruff
* pre-commit
* GitHub Actions

Implement

* FastAPI application
* centralized settings
* structured logging
* database engine
* session factory
* declarative base
* Alembic
* PostgreSQL container
* Redis container
* Dockerfile
* Docker Compose
* /health
* pytest
* Ruff
* pre-commit
* CI workflow

Health Endpoint

GET /health

Expected:

{
“status”: “ok”,
“service”: “alyntiq-api”
}

Do Not Implement

* market data
* Alpaca
* ML
* strategies
* backtesting
* risk
* execution
* frontend

Definition of Done

* application runs
* Docker Compose works
* /health returns 200
* PostgreSQL healthy
* Redis healthy
* Alembic works
* tests pass
* Ruff passes
* CI configured
* no secrets committed