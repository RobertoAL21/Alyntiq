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

Frontend

* Next.js
* React
* TypeScript
* Tailwind CSS
* Lightweight Charts or similar financial charting library

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