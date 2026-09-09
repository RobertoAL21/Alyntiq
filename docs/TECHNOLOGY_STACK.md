Alyntiq — Technology Stack

Backend

* Python 3.12+
* FastAPI
* Pydantic
* Pydantic Settings
* SQLAlchemy 2.x
* Alembic

Database

* PostgreSQL
* TimescaleDB may be introduced if justified by time-series workloads.

Cache / Background Infrastructure

* Redis

Machine Learning

* Pandas
* NumPy
* Scikit-learn
* XGBoost
* LightGBM

Future research:

* PyTorch
* LSTM
* GRU
* Temporal CNN
* time-series Transformers

Optimization

* Optuna

Experiment Tracking

* MLflow

Market Data and Trading

Initial provider:

* Alpaca

Capabilities:

* historical market data
* latest quotes
* WebSockets
* paper trading

Provider-specific code must remain behind abstractions.

## Frontend

- React

- TypeScript

- Vite

- React Router

- Tailwind CSS

- Lightweight Charts or similar financial charting library

The frontend will be a standalone Single Page Application (SPA).

FastAPI will provide the backend API and React will consume it through HTTP APIs and WebSockets.

Next.js is intentionally not part of the frontend stack.

Infrastructure

* Docker
* Docker Compose
* GitHub Actions

Future cloud:

* AWS
* RDS
* ECS or EC2
* ElastiCache
* S3
* CloudWatch

Testing

* pytest
* FastAPI TestClient
* Ruff
* pre-commit

Observability

Initially:

* structured Python logging

Later:

* OpenTelemetry
* Prometheus
* Grafana

LLM observability tools should only be introduced if the NLP phase requires them.