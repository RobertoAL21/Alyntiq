from app.core.config import Settings


def test_settings_default_to_paper_trading() -> None:
    settings = Settings(_env_file=None)

    assert settings.trading_environment == "paper"
    assert settings.alpaca_data_feed == "iex"
    assert settings.mlflow_tracking_uri == "sqlite:///mlruns/mlflow.db"
    assert settings.mlflow_artifact_uri == "file:./mlruns/artifacts"
    assert settings.otel_service_name == "alyntiq-api"
    assert settings.otel_exporter_otlp_endpoint is None
    assert settings.dashboard_control_token is None


def test_settings_read_runtime_environment(monkeypatch) -> None:
    monkeypatch.setenv("APP_NAME", "Test Alyntiq API")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://test:test@localhost:5432/test")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4318")
    monkeypatch.setenv("DASHBOARD_CONTROL_TOKEN", "local-control")

    settings = Settings(_env_file=None)

    assert settings.app_name == "Test Alyntiq API"
    assert settings.debug is True
    assert settings.database_url == "postgresql+psycopg://test:test@localhost:5432/test"
    assert settings.otel_exporter_otlp_endpoint == "http://collector:4318"
    assert settings.dashboard_control_token == "local-control"


def test_settings_treats_a_blank_otlp_endpoint_as_unset(monkeypatch) -> None:
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")

    settings = Settings(_env_file=None)

    assert settings.otel_exporter_otlp_endpoint is None
