# Observability

## Scope

Phase 22 adds vendor-neutral OpenTelemetry metrics and FastAPI tracing instrumentation to
the existing application. It observes operational behavior; it does not change model
predictions, strategy decisions, risk policies, execution semantics, or portfolio
accounting.

```text
API / models / risk / execution / market data / backtests
                         |
                         v
                  Telemetry interface
                         |
                         v
              OpenTelemetry SDK + optional OTLP
```

## Signals

The `OpenTelemetryTelemetry` implementation emits these metrics:

- HTTP request duration by method, route, and response status;
- model prediction count and inference duration by model name and version;
- submitted paper trades by symbol and side;
- risk-rejected trades by limiting reason;
- historical-ingestion failures by provider type;
- real-time WebSocket reconnects by data feed; and
- latest reported portfolio PnL and drawdown by explicit portfolio identifier.

The in-memory backtest records its final PnL and maximum drawdown as a `backtest:<symbol>`
snapshot. A live portfolio orchestration layer does not yet exist, so it must call
`record_portfolio_snapshot` with a stable portfolio identifier when introduced.

## Runtime configuration

`OTEL_SERVICE_NAME` defaults to `alyntiq-api`. Set `OTEL_EXPORTER_OTLP_ENDPOINT` to an OTLP
HTTP collector base URL to export traces and metrics; Alyntiq appends `/v1/traces` and
`/v1/metrics`. Without that setting, the SDK remains instrumented but exports nowhere.

FastAPI is instrumented once during application lifespan startup. The explicit latency
middleware records a stable path, never query parameters, to avoid telemetry cardinality
growth. Domain modules depend only on the small `Telemetry` interface and use a no-op
implementation until the application or a CLI process configures OpenTelemetry.

## Boundaries

Prometheus, Grafana dashboards, alert rules, collectors, drift analysis, deployment, and
CI/CD are intentionally not configured here. An OTLP collector or compatible backend is
an external runtime concern. Telemetry attributes exclude credentials, request bodies,
feature values, target values, predictions, and order quantities.

## Verification

From `backend/`, run:

```bash
ruff format --check .
ruff check .
pytest tests/test_observability.py
```
