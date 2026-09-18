# ADR 023 — Use OpenTelemetry with Optional OTLP Export

## Status

Accepted

## Context

Alyntiq has structured logs but no shared operational metric contract. The project needs
visibility across HTTP, model evaluation, risk, execution, market-data reliability, and
portfolio results without coupling those domains to a particular dashboard vendor.

## Options Considered

### Continue with JSON logs only

Logs provide event detail but do not supply aggregation-friendly latency, volume, PnL, or
drawdown measurements.

### Couple application code directly to Prometheus or Grafana

This would provide a backend-specific solution before collector, dashboard, deployment,
and alerting requirements are defined.

### Use OpenTelemetry metrics and traces with optional OTLP export

This provides stable instrumentation names and attributes while keeping exporters and
backends configurable at runtime.

## Decision

Introduce OpenTelemetry API, SDK, OTLP/HTTP exporter, and FastAPI instrumentation. Expose a
small telemetry interface for domain code, configure one process-wide provider during
application or CLI startup, and use the no-op implementation before configuration.

Only configure OTLP exporters when `OTEL_EXPORTER_OTLP_ENDPOINT` is set. Capture explicit
business metrics for predictions, trades, rejections, ingestion failures, reconnects, PnL,
and drawdown, plus HTTP and model latency. Do not attach secrets, request bodies, market
features, targets, raw predictions, or order quantities as telemetry attributes.

## Consequences

Telemetry is vendor-neutral and can later feed an OpenTelemetry Collector, Prometheus, or
Grafana-compatible backend without changing domain behavior. Without an OTLP endpoint,
metrics remain local to the SDK and are not externally retained. Dashboards, alerting,
drift detection, deployment, and CI/CD are deferred.
