from app.core.config import Settings


def test_settings_default_to_paper_trading() -> None:
    settings = Settings(_env_file=None)

    assert settings.trading_environment == "paper"
    assert settings.alpaca_data_feed == "iex"
    assert settings.mlflow_tracking_uri == "sqlite:///mlruns/mlflow.db"
    assert settings.mlflow_artifact_uri == "file:./mlruns/artifacts"


def test_settings_read_runtime_environment(monkeypatch) -> None:
    monkeypatch.setenv("APP_NAME", "Test Alyntiq API")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://test:test@localhost:5432/test")

    settings = Settings(_env_file=None)

    assert settings.app_name == "Test Alyntiq API"
    assert settings.debug is True
    assert settings.database_url == "postgresql+psycopg://test:test@localhost:5432/test"
