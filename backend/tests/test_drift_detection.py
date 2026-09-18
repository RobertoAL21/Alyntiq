import pandas as pd
import pytest

from app.drift import DriftConfig, DriftDetectionError, DriftDetectionService, DriftKind
from app.regimes import MarketRegime


def test_drift_service_generates_alerts_for_each_monitored_signal() -> None:
    service = DriftDetectionService(
        DriftConfig(
            distribution_bins=4,
            feature_psi_threshold=0.1,
            prediction_psi_threshold=0.1,
            volatility_relative_change_threshold=0.5,
        )
    )

    report = service.evaluate(
        reference_features=pd.DataFrame({"momentum": [0.0] * 20, "stable": [1.0, 2.0] * 10}),
        current_features=pd.DataFrame({"momentum": [2.0] * 20, "stable": [1.0, 2.0] * 10}),
        reference_predictions=pd.Series([0.1] * 20),
        current_predictions=pd.Series([0.9] * 20),
        reference_volatility=pd.Series([0.1] * 20),
        current_volatility=pd.Series([0.3] * 20),
        reference_regimes=(MarketRegime.BULL,) * 20,
        current_regimes=(MarketRegime.BEAR,) * 20,
    )

    feature_drift = {item.name: item for item in report.feature_distributions}
    assert feature_drift["momentum"].drifted
    assert not feature_drift["stable"].drifted
    assert report.prediction_distribution is not None
    assert report.prediction_distribution.drifted
    assert report.volatility is not None
    assert report.volatility.relative_change == pytest.approx(2.0)
    assert report.volatility.drifted
    assert report.market_regime is not None
    assert report.market_regime.changed
    assert {(alert.kind, alert.subject) for alert in report.alerts} == {
        (DriftKind.FEATURE, "momentum"),
        (DriftKind.PREDICTION, "prediction"),
        (DriftKind.VOLATILITY, "volatility"),
        (DriftKind.MARKET_REGIME, "market_regime"),
    }


def test_drift_service_returns_no_alert_for_matching_samples() -> None:
    sample = pd.DataFrame(
        {"return": [-0.01, 0.0, 0.01, 0.02], "volume_ratio": [0.8, 1.0, 1.2, 1.1]}
    )

    report = DriftDetectionService().evaluate(
        reference_features=sample,
        current_features=sample.copy(),
        reference_predictions=pd.Series([0.4, 0.5, 0.6, 0.5]),
        current_predictions=pd.Series([0.4, 0.5, 0.6, 0.5]),
        reference_volatility=pd.Series([0.1, 0.2, 0.1, 0.2]),
        current_volatility=pd.Series([0.1, 0.2, 0.1, 0.2]),
        reference_regimes=(MarketRegime.SIDEWAYS,) * 4,
        current_regimes=(MarketRegime.SIDEWAYS,) * 4,
    )

    assert not report.alerts
    assert all(not item.drifted for item in report.feature_distributions)


def test_drift_service_rejects_unsafe_or_incomplete_comparisons() -> None:
    service = DriftDetectionService()

    with pytest.raises(DriftDetectionError, match="columns must match"):
        service.evaluate(
            reference_features=pd.DataFrame({"first": [1.0]}),
            current_features=pd.DataFrame({"second": [1.0]}),
        )
    with pytest.raises(DriftDetectionError, match="supplied together"):
        service.evaluate(
            reference_features=pd.DataFrame({"feature": [1.0]}),
            current_features=pd.DataFrame({"feature": [1.0]}),
            reference_predictions=pd.Series([0.5]),
        )
    with pytest.raises(DriftDetectionError, match="non-negative"):
        service.evaluate(
            reference_features=pd.DataFrame({"feature": [1.0]}),
            current_features=pd.DataFrame({"feature": [1.0]}),
            reference_volatility=pd.Series([0.1]),
            current_volatility=pd.Series([-0.1]),
        )
