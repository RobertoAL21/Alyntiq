from datetime import UTC, datetime, timedelta
from math import sin

import pytest

from app.regimes import (
    MarketRegime,
    MarketRegimeDetector,
    RegimeBar,
    RegimeDetectionError,
    RegimeFeatureCalculationError,
    RegimeFeatureConfig,
    RegimeFeatures,
    RegimeMethod,
    RegimeModelConfig,
    VolatilityRegime,
    calculate_regime_features,
)


def timestamp(day: int) -> datetime:
    return datetime(2024, 1, 2, tzinfo=UTC) + timedelta(days=day)


def make_bars(periods: int = 60) -> tuple[RegimeBar, ...]:
    bars = []
    for day in range(periods):
        spy_close = 100 + day * 0.3 + sin(day / 2)
        qqq_close = 200 + day * 0.5 + sin(day / 3)
        bars.extend(
            (
                RegimeBar(timestamp(day), "SPY", spy_close, 1_000_000 + day * 1_000),
                RegimeBar(timestamp(day), "QQQ", qqq_close, 2_000_000 + day * 1_500),
            )
        )
    return tuple(bars)


def feature(day: int, trend: float, volatility: float = 0.2) -> RegimeFeatures:
    return RegimeFeatures(
        timestamp=timestamp(day),
        return_value=trend / 2,
        trend=trend,
        volatility=volatility,
        volume_ratio=1 + trend,
        correlation=0.8,
    )


def test_regime_features_are_trailing_and_include_all_required_market_inputs() -> None:
    config = RegimeFeatureConfig(window=5)
    baseline = calculate_regime_features(make_bars(), config)
    cutoff = timestamp(30)
    modified = list(make_bars())
    for index, bar in enumerate(modified):
        if bar.timestamp > cutoff:
            modified[index] = RegimeBar(bar.timestamp, bar.symbol, bar.close * 10, bar.volume * 10)
    candidate = calculate_regime_features(modified, config)

    assert baseline
    assert [item for item in baseline if item.timestamp <= cutoff] == [
        item for item in candidate if item.timestamp <= cutoff
    ]
    sample = baseline[-1]
    assert sample.volatility >= 0
    assert sample.volume_ratio > 0
    assert -1 <= sample.correlation <= 1


def test_regime_features_reject_missing_or_duplicate_market_context() -> None:
    config = RegimeFeatureConfig(window=5)
    bars = make_bars(10)

    with pytest.raises(RegimeFeatureCalculationError, match="missing configured symbols"):
        calculate_regime_features([bar for bar in bars if bar.symbol != "QQQ"], config)
    with pytest.raises(RegimeFeatureCalculationError, match="unique per symbol"):
        calculate_regime_features((*bars, bars[0]), config)


def test_kmeans_and_gaussian_mixture_map_trend_extremes_to_descriptive_regimes() -> None:
    training = (
        *(feature(day, -0.20 - day * 0.01, 0.10) for day in range(3)),
        *(feature(day + 3, -0.01 + day * 0.005, 0.20) for day in range(3)),
        *(feature(day + 6, 0.15 + day * 0.01, 0.30) for day in range(3)),
    )
    candidates = (feature(9, -0.18, 0.10), feature(10, 0, 0.20), feature(11, 0.18, 0.30))

    for method in (RegimeMethod.KMEANS, RegimeMethod.GAUSSIAN_MIXTURE):
        detector = MarketRegimeDetector(RegimeModelConfig(method=method, random_seed=7))
        detector.fit(training)
        classifications = detector.classify(candidates)

        assert [item.market_regime for item in classifications] == [
            MarketRegime.BEAR,
            MarketRegime.SIDEWAYS,
            MarketRegime.BULL,
        ]
        assert [item.volatility_regime for item in classifications] == [
            VolatilityRegime.LOW,
            VolatilityRegime.HIGH,
            VolatilityRegime.HIGH,
        ]
        assert all(item.cluster_id is not None for item in classifications)
        assert all(item.membership_strength is None for item in classifications)


def test_hdbscan_classifies_later_observations_without_refitting() -> None:
    training = tuple(
        feature(day, -0.15 + (day % 8) * 0.04, 0.1 + (day % 3) * 0.1) for day in range(24)
    )
    detector = MarketRegimeDetector(
        RegimeModelConfig(method=RegimeMethod.HDBSCAN, min_cluster_size=4)
    )
    detector.fit(training)

    classifications = detector.classify((feature(24, 0.05, 0.2), feature(25, -0.1, 0.1)))

    assert [item.timestamp for item in classifications] == [timestamp(24), timestamp(25)]
    assert all(
        item.membership_strength is None or 0 <= item.membership_strength <= 1
        for item in classifications
    )


def test_detector_requires_chronological_explicit_training_before_classification() -> None:
    detector = MarketRegimeDetector(RegimeModelConfig(method=RegimeMethod.KMEANS))
    with pytest.raises(RegimeDetectionError, match="must be fitted"):
        detector.classify((feature(0, 0.1),))
    with pytest.raises(RegimeDetectionError, match="strictly increasing"):
        detector.fit((feature(2, 0.1), feature(1, 0.2), feature(3, 0.3)))
