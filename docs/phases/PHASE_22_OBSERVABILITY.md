Phase 22 — Observability

Status: COMPLETE

Track:

* predictions
* trades
* rejected trades
* API latency
* ingestion failures
* WebSocket reconnects
* model latency
* PnL
* portfolio drawdown

Introduce:

OpenTelemetry.

Potential later stack:

Prometheus + Grafana.

Delivered:

* OpenTelemetry SDK, FastAPI tracing instrumentation, and optional OTLP/HTTP export;
* metrics for predictions, submitted and risk-rejected trades, HTTP and model latency,
  historical-ingestion failures, and real-time reconnects; and
* PnL and drawdown snapshot gauges for backtests and future explicit portfolio reporters.

Prometheus, Grafana dashboards, alerting, drift analysis, deployment, and CI/CD remain out
of scope.
