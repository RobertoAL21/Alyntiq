from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from threading import Lock
from typing import Protocol

from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.metrics import Observation
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.config import Settings


class Telemetry(Protocol):
    """Small domain-neutral telemetry interface used by operational components."""

    def record_api_latency(
        self, *, method: str, route: str, status_code: int, duration_seconds: float
    ) -> None: ...

    def record_prediction(
        self,
        *,
        model_name: str,
        model_version: str,
        count: int,
        duration_seconds: float,
    ) -> None: ...

    def record_trade(self, *, symbol: str, side: str) -> None: ...

    def record_rejected_trade(self, *, reason: str) -> None: ...

    def record_ingestion_failure(self, *, source: str) -> None: ...

    def record_websocket_reconnect(self, *, feed: str) -> None: ...

    def record_portfolio_snapshot(
        self, *, portfolio_id: str, pnl: Decimal, drawdown: Decimal
    ) -> None: ...


class NoopTelemetry:
    """Safe default for library use before an application configures OpenTelemetry."""

    def record_api_latency(self, **_: object) -> None:
        return None

    def record_prediction(self, **_: object) -> None:
        return None

    def record_trade(self, **_: object) -> None:
        return None

    def record_rejected_trade(self, **_: object) -> None:
        return None

    def record_ingestion_failure(self, **_: object) -> None:
        return None

    def record_websocket_reconnect(self, **_: object) -> None:
        return None

    def record_portfolio_snapshot(self, **_: object) -> None:
        return None


@dataclass(frozen=True)
class PortfolioSnapshot:
    pnl: float
    drawdown: float


class OpenTelemetryTelemetry:
    """Create stable application metrics without embedding exporter details in domains."""

    def __init__(self, meter: metrics.Meter) -> None:
        self._api_latency = meter.create_histogram(
            "alyntiq.api.request.duration", unit="s", description="HTTP request duration"
        )
        self._predictions = meter.create_counter(
            "alyntiq.model.predictions", unit="{prediction}", description="Model predictions"
        )
        self._model_latency = meter.create_histogram(
            "alyntiq.model.inference.duration", unit="s", description="Model inference duration"
        )
        self._trades = meter.create_counter(
            "alyntiq.paper.trades", unit="{trade}", description="Paper broker order submissions"
        )
        self._rejected_trades = meter.create_counter(
            "alyntiq.risk.rejected_trades", unit="{trade}", description="Risk-rejected orders"
        )
        self._ingestion_failures = meter.create_counter(
            "alyntiq.market_data.ingestion.failures",
            unit="{failure}",
            description="Historical data ingestion failures",
        )
        self._websocket_reconnects = meter.create_counter(
            "alyntiq.market_data.websocket.reconnects",
            unit="{reconnect}",
            description="Real-time market-data reconnects",
        )
        self._portfolio_snapshots: dict[str, PortfolioSnapshot] = {}
        self._snapshot_lock = Lock()
        meter.create_observable_gauge(
            "alyntiq.portfolio.pnl",
            callbacks=[self._observe_pnl],
            unit="USD",
            description="Latest observed portfolio profit and loss",
        )
        meter.create_observable_gauge(
            "alyntiq.portfolio.drawdown",
            callbacks=[self._observe_drawdown],
            unit="1",
            description="Latest observed portfolio drawdown as a negative fraction",
        )

    def record_api_latency(
        self, *, method: str, route: str, status_code: int, duration_seconds: float
    ) -> None:
        self._api_latency.record(
            duration_seconds,
            {
                "http.request.method": method,
                "http.route": route,
                "http.response.status_code": status_code,
            },
        )

    def record_prediction(
        self,
        *,
        model_name: str,
        model_version: str,
        count: int,
        duration_seconds: float,
    ) -> None:
        attributes = {"model.name": model_name, "model.version": model_version}
        self._predictions.add(count, attributes)
        self._model_latency.record(duration_seconds, attributes)

    def record_trade(self, *, symbol: str, side: str) -> None:
        self._trades.add(1, {"symbol": symbol, "order.side": side})

    def record_rejected_trade(self, *, reason: str) -> None:
        self._rejected_trades.add(1, {"risk.reason": reason})

    def record_ingestion_failure(self, *, source: str) -> None:
        self._ingestion_failures.add(1, {"market_data.source": source})

    def record_websocket_reconnect(self, *, feed: str) -> None:
        self._websocket_reconnects.add(1, {"market_data.feed": feed})

    def record_portfolio_snapshot(
        self, *, portfolio_id: str, pnl: Decimal, drawdown: Decimal
    ) -> None:
        if not portfolio_id.strip():
            raise ValueError("portfolio_id must not be blank")
        if drawdown > 0:
            raise ValueError("portfolio drawdown must be zero or negative")
        snapshot = PortfolioSnapshot(
            pnl=float(pnl),
            drawdown=float(drawdown),
        )
        with self._snapshot_lock:
            self._portfolio_snapshots[portfolio_id.strip()] = snapshot

    def _observe_pnl(self, _: metrics.CallbackOptions) -> Iterable[Observation]:
        with self._snapshot_lock:
            return tuple(
                Observation(snapshot.pnl, {"portfolio.id": portfolio_id})
                for portfolio_id, snapshot in self._portfolio_snapshots.items()
            )

    def _observe_drawdown(self, _: metrics.CallbackOptions) -> Iterable[Observation]:
        with self._snapshot_lock:
            return tuple(
                Observation(snapshot.drawdown, {"portfolio.id": portfolio_id})
                for portfolio_id, snapshot in self._portfolio_snapshots.items()
            )


_telemetry: Telemetry = NoopTelemetry()
_configured = False


def configure_observability(settings: Settings, app: FastAPI | None = None) -> Telemetry:
    """Configure one process-wide OpenTelemetry provider and optionally instrument FastAPI."""
    global _configured, _telemetry
    if not _configured:
        resource = Resource.create({"service.name": settings.otel_service_name})
        meter_provider = MeterProvider(resource=resource, metric_readers=_metric_readers(settings))
        tracer_provider = TracerProvider(resource=resource)
        if settings.otel_exporter_otlp_endpoint is not None:
            tracer_provider.add_span_processor(
                BatchSpanProcessor(
                    OTLPSpanExporter(endpoint=_trace_endpoint(settings.otel_exporter_otlp_endpoint))
                )
            )
        metrics.set_meter_provider(meter_provider)
        trace.set_tracer_provider(tracer_provider)
        _telemetry = OpenTelemetryTelemetry(metrics.get_meter("alyntiq.observability"))
        _configured = True
    if app is not None and not getattr(app.state, "otel_instrumented", False):
        FastAPIInstrumentor.instrument_app(app)
        app.state.otel_instrumented = True
    return _telemetry


def get_telemetry() -> Telemetry:
    return _telemetry


def _metric_readers(settings: Settings) -> tuple[PeriodicExportingMetricReader, ...]:
    if settings.otel_exporter_otlp_endpoint is None:
        return ()
    return (
        PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=_metric_endpoint(settings.otel_exporter_otlp_endpoint))
        ),
    )


def _trace_endpoint(base_endpoint: str) -> str:
    return f"{base_endpoint.rstrip('/')}/v1/traces"


def _metric_endpoint(base_endpoint: str) -> str:
    return f"{base_endpoint.rstrip('/')}/v1/metrics"
