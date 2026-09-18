from collections import Counter
from collections.abc import Sequence

import numpy as np
import pandas as pd

from app.drift.types import (
    DistributionDrift,
    DriftAlert,
    DriftConfig,
    DriftKind,
    DriftReport,
    MarketRegimeDrift,
    VolatilityDrift,
)
from app.regimes.types import MarketRegime, RegimeClassification

RegimeSample = MarketRegime | RegimeClassification


class DriftDetectionError(ValueError):
    """Raised when samples cannot be compared safely."""


class DriftDetectionService:
    """Compare fixed training references with later observations without side effects."""

    def __init__(self, config: DriftConfig | None = None) -> None:
        self._config = config or DriftConfig()

    def evaluate(
        self,
        *,
        reference_features: pd.DataFrame,
        current_features: pd.DataFrame,
        reference_predictions: pd.Series | None = None,
        current_predictions: pd.Series | None = None,
        reference_volatility: pd.Series | None = None,
        current_volatility: pd.Series | None = None,
        reference_regimes: Sequence[RegimeSample] | None = None,
        current_regimes: Sequence[RegimeSample] | None = None,
    ) -> DriftReport:
        """Evaluate independent data and model signals against an explicit reference period."""
        reference_frame, current_frame = _validated_feature_frames(
            reference_features, current_features
        )
        feature_distributions = tuple(
            self._distribution(
                name=column,
                reference=reference_frame[column],
                current=current_frame[column],
                threshold=self._config.feature_psi_threshold,
            )
            for column in reference_frame.columns
        )

        prediction_distribution = self._optional_distribution(
            name="prediction",
            reference=reference_predictions,
            current=current_predictions,
            threshold=self._config.prediction_psi_threshold,
        )
        volatility = self._optional_volatility(reference_volatility, current_volatility)
        market_regime = _optional_market_regime(reference_regimes, current_regimes)

        alerts = _build_alerts(
            feature_distributions,
            prediction_distribution,
            volatility,
            market_regime,
            self._config,
        )
        return DriftReport(
            feature_distributions=feature_distributions,
            prediction_distribution=prediction_distribution,
            volatility=volatility,
            market_regime=market_regime,
            alerts=alerts,
        )

    def _distribution(
        self,
        *,
        name: str,
        reference: pd.Series,
        current: pd.Series,
        threshold: float,
    ) -> DistributionDrift:
        reference_values = _numeric_values(reference, f"reference {name}")
        current_values = _numeric_values(current, f"current {name}")
        psi = population_stability_index(
            reference_values, current_values, bins=self._config.distribution_bins
        )
        return DistributionDrift(
            name=name,
            population_stability_index=psi,
            reference_mean=float(np.mean(reference_values)),
            current_mean=float(np.mean(current_values)),
            drifted=psi >= threshold,
        )

    def _optional_distribution(
        self,
        *,
        name: str,
        reference: pd.Series | None,
        current: pd.Series | None,
        threshold: float,
    ) -> DistributionDrift | None:
        _require_pair(reference, current, name)
        if reference is None:
            return None
        return self._distribution(
            name=name, reference=reference, current=current, threshold=threshold
        )

    def _optional_volatility(
        self, reference: pd.Series | None, current: pd.Series | None
    ) -> VolatilityDrift | None:
        _require_pair(reference, current, "volatility")
        if reference is None:
            return None
        reference_values = _numeric_values(reference, "reference volatility")
        current_values = _numeric_values(current, "current volatility")
        if np.any(reference_values < 0) or np.any(current_values < 0):
            raise DriftDetectionError("volatility values must be non-negative")
        reference_mean = float(np.mean(reference_values))
        current_mean = float(np.mean(current_values))
        relative_change = abs(current_mean - reference_mean) / max(abs(reference_mean), 1e-12)
        return VolatilityDrift(
            reference_mean=reference_mean,
            current_mean=current_mean,
            relative_change=relative_change,
            drifted=relative_change >= self._config.volatility_relative_change_threshold,
        )


def population_stability_index(reference: np.ndarray, current: np.ndarray, *, bins: int) -> float:
    """Return PSI using bins learned only from the reference distribution."""
    if bins < 2:
        raise ValueError("bins must be at least 2")
    if np.ptp(reference) == 0:
        center = float(np.mean(reference))
        thresholds = np.array([center + max(abs(center) * 0.01, 1e-12)])
    else:
        thresholds = np.unique(np.quantile(reference, np.linspace(0, 1, bins + 1)[1:-1]))
    edges = np.concatenate(([-np.inf], thresholds, [np.inf]))
    reference_counts, _ = np.histogram(reference, bins=edges)
    current_counts, _ = np.histogram(current, bins=edges)
    epsilon = 1e-6
    reference_proportion = (reference_counts + epsilon) / (
        reference_counts.sum() + epsilon * len(reference_counts)
    )
    current_proportion = (current_counts + epsilon) / (
        current_counts.sum() + epsilon * len(current_counts)
    )
    return float(
        np.sum(
            (current_proportion - reference_proportion)
            * np.log(current_proportion / reference_proportion)
        )
    )


def _validated_feature_frames(
    reference: pd.DataFrame, current: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if reference.empty or current.empty:
        raise DriftDetectionError("reference and current feature samples must not be empty")
    if tuple(reference.columns) != tuple(current.columns):
        raise DriftDetectionError(
            "reference and current feature columns must match in the same order"
        )
    if not len(reference.columns):
        raise DriftDetectionError("feature samples must contain at least one column")
    reference_values = pd.DataFrame(
        {
            column: _numeric_values(reference[column], f"reference feature {column}")
            for column in reference
        }
    )
    current_values = pd.DataFrame(
        {
            column: _numeric_values(current[column], f"current feature {column}")
            for column in current
        }
    )
    return reference_values, current_values


def _numeric_values(values: pd.Series, name: str) -> np.ndarray:
    try:
        numeric = pd.to_numeric(values, errors="raise").to_numpy(dtype=float)
    except (TypeError, ValueError) as error:
        raise DriftDetectionError(f"{name} must contain numeric values") from error
    if not len(numeric):
        raise DriftDetectionError(f"{name} must not be empty")
    if not np.isfinite(numeric).all():
        raise DriftDetectionError(f"{name} must contain only finite values")
    return numeric


def _require_pair(reference: object | None, current: object | None, name: str) -> None:
    if (reference is None) != (current is None):
        raise DriftDetectionError(f"reference and current {name} must be supplied together")


def _optional_market_regime(
    reference: Sequence[RegimeSample] | None,
    current: Sequence[RegimeSample] | None,
) -> MarketRegimeDrift | None:
    _require_pair(reference, current, "regimes")
    if reference is None:
        return None
    if not reference or not current:
        raise DriftDetectionError("reference and current regime samples must not be empty")
    reference_regime = _dominant_regime(reference)
    current_regime = _dominant_regime(current)
    return MarketRegimeDrift(
        reference_regime=reference_regime,
        current_regime=current_regime,
        changed=reference_regime is not current_regime,
    )


def _dominant_regime(classifications: Sequence[RegimeSample]) -> MarketRegime:
    try:
        counts = Counter(
            item.market_regime if isinstance(item, RegimeClassification) else MarketRegime(item)
            for item in classifications
        )
    except ValueError as error:
        raise DriftDetectionError("regime samples must use a supported market regime") from error
    return min(counts, key=lambda regime: (-counts[regime], regime.value))


def _build_alerts(
    feature_distributions: tuple[DistributionDrift, ...],
    prediction_distribution: DistributionDrift | None,
    volatility: VolatilityDrift | None,
    market_regime: MarketRegimeDrift | None,
    config: DriftConfig,
) -> tuple[DriftAlert, ...]:
    alerts = [
        DriftAlert(
            kind=DriftKind.FEATURE,
            subject=item.name,
            value=item.population_stability_index,
            threshold=config.feature_psi_threshold,
        )
        for item in feature_distributions
        if item.drifted
    ]
    if prediction_distribution is not None and prediction_distribution.drifted:
        alerts.append(
            DriftAlert(
                kind=DriftKind.PREDICTION,
                subject="prediction",
                value=prediction_distribution.population_stability_index,
                threshold=config.prediction_psi_threshold,
            )
        )
    if volatility is not None and volatility.drifted:
        alerts.append(
            DriftAlert(
                kind=DriftKind.VOLATILITY,
                subject="volatility",
                value=volatility.relative_change,
                threshold=config.volatility_relative_change_threshold,
            )
        )
    if market_regime is not None and market_regime.changed:
        alerts.append(
            DriftAlert(
                kind=DriftKind.MARKET_REGIME,
                subject="market_regime",
                value=market_regime.current_regime.value,
                threshold=market_regime.reference_regime.value,
            )
        )
    return tuple(alerts)
