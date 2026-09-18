from decimal import Decimal

from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

from app.observability.telemetry import NoopTelemetry, OpenTelemetryTelemetry


def test_open_telemetry_records_all_phase_metrics() -> None:
    reader = InMemoryMetricReader()
    provider = MeterProvider(metric_readers=[reader])
    telemetry = OpenTelemetryTelemetry(provider.get_meter("test-observability"))

    telemetry.record_api_latency(
        method="GET", route="/health", status_code=200, duration_seconds=0.01
    )
    telemetry.record_prediction(
        model_name="transformer",
        model_version="temporal-v1",
        count=3,
        duration_seconds=0.02,
    )
    telemetry.record_trade(symbol="AAPL", side="buy")
    telemetry.record_rejected_trade(reason="maximum_drawdown")
    telemetry.record_ingestion_failure(source="AlpacaMarketDataProvider")
    telemetry.record_websocket_reconnect(feed="iex")
    telemetry.record_portfolio_snapshot(
        portfolio_id="paper-main",
        pnl=Decimal("12.50"),
        drawdown=Decimal("-0.03"),
    )

    metrics = _metric_values(reader)

    assert set(metrics) == {
        "alyntiq.api.request.duration",
        "alyntiq.model.predictions",
        "alyntiq.model.inference.duration",
        "alyntiq.paper.trades",
        "alyntiq.risk.rejected_trades",
        "alyntiq.market_data.ingestion.failures",
        "alyntiq.market_data.websocket.reconnects",
        "alyntiq.portfolio.pnl",
        "alyntiq.portfolio.drawdown",
    }
    assert metrics["alyntiq.model.predictions"] == [3]
    assert metrics["alyntiq.portfolio.pnl"] == [12.5]
    assert metrics["alyntiq.portfolio.drawdown"] == [-0.03]


def test_noop_telemetry_is_safe_before_runtime_configuration() -> None:
    telemetry = NoopTelemetry()

    telemetry.record_api_latency(method="GET", route="/health", status_code=200, duration_seconds=0)
    telemetry.record_prediction(model_name="model", model_version="v1", count=1, duration_seconds=0)
    telemetry.record_trade(symbol="AAPL", side="buy")
    telemetry.record_rejected_trade(reason="limit")
    telemetry.record_ingestion_failure(source="provider")
    telemetry.record_websocket_reconnect(feed="iex")
    telemetry.record_portfolio_snapshot(
        portfolio_id="paper-main", pnl=Decimal("0"), drawdown=Decimal("0")
    )


def _metric_values(reader: InMemoryMetricReader) -> dict[str, list[float | int]]:
    data = reader.get_metrics_data()
    assert data is not None
    values: dict[str, list[float | int]] = {}
    for resource_metric in data.resource_metrics:
        for scope_metric in resource_metric.scope_metrics:
            for metric in scope_metric.metrics:
                values[metric.name] = [
                    point.value if hasattr(point, "value") else point.sum
                    for point in metric.data.data_points
                ]
    return values
