import pandas as pd
import pandas.testing as pdt
import pytest
from conftest import make_feature_bars

from app.features.calculator import (
    FeatureCalculationError,
    calculate_features,
    feature_columns_present,
)
from app.features.constants import FEATURE_COLUMNS


def test_calculates_the_phase_three_feature_contract() -> None:
    features = calculate_features(make_feature_bars())
    aapl = features.loc[features["symbol"] == "AAPL"].reset_index(drop=True)

    assert feature_columns_present(features)
    assert set(FEATURE_COLUMNS).issubset(features.columns)
    assert len(features) == 240
    assert aapl.loc[5, "returns_5d"] == pytest.approx(0.05)
    assert aapl.loc[9, "sma_10"] == pytest.approx(104.5)
    assert aapl.loc[19, "volume_ratio"] == pytest.approx(1_019_000 / 1_009_500)
    assert aapl.loc[20, "spy_returns_1d"] == pytest.approx(0.5 / 409.5)
    assert aapl.loc[20, "qqq_returns_1d"] == pytest.approx(0.75 / 364.25)
    expected_spy_volatility = (
        pd.Series([0.5 / (400 + (0.5 * index)) for index in range(20)]).std(ddof=0) * 252**0.5
    )
    assert aapl.loc[20, "spy_volatility_20"] == pytest.approx(expected_spy_volatility)


def test_future_bars_do_not_change_features_available_at_an_earlier_timestamp() -> None:
    bars = make_feature_bars()
    baseline = calculate_features(bars)
    cutoff = pd.Timestamp("2024-03-15", tz="UTC")

    modified = bars.copy()
    future_rows = modified["timestamp"] > cutoff
    modified.loc[future_rows, "close"] = modified.loc[future_rows, "close"] * 10
    modified.loc[future_rows, "high"] = modified.loc[future_rows, "high"] * 10
    modified.loc[future_rows, "low"] = modified.loc[future_rows, "low"] * 10
    modified.loc[future_rows, "volume"] = modified.loc[future_rows, "volume"] * 10
    candidate = calculate_features(modified)

    columns = ["symbol", "timestamp", *FEATURE_COLUMNS]
    expected = baseline.loc[baseline["timestamp"] <= cutoff, columns].reset_index(drop=True)
    actual = candidate.loc[candidate["timestamp"] <= cutoff, columns].reset_index(drop=True)
    pdt.assert_frame_equal(actual, expected)


def test_rejects_bars_without_required_provenance() -> None:
    bars = make_feature_bars().drop(columns="source")

    with pytest.raises(FeatureCalculationError, match="source"):
        calculate_features(bars)
