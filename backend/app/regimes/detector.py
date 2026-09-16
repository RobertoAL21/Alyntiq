from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from sklearn.cluster import HDBSCAN, KMeans
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

from app.regimes.types import (
    MarketRegime,
    RegimeClassification,
    RegimeFeatures,
    RegimeMethod,
    RegimeModelConfig,
    VolatilityRegime,
)

FEATURE_NAMES = ("return_value", "trend", "volatility", "volume_ratio", "correlation")


class RegimeDetectionError(ValueError):
    """Raised when a regime model cannot be fitted or used reproducibly."""


@dataclass
class MarketRegimeDetector:
    """Fit an unsupervised regime model on one period, then classify later observations."""

    config: RegimeModelConfig
    _scaler: StandardScaler | None = None
    _model: KMeans | GaussianMixture | HDBSCAN | None = None
    _cluster_labels: dict[int, MarketRegime] | None = None
    _hdbscan_centers: dict[int, np.ndarray] | None = None
    _volatility_threshold: float | None = None

    def fit(self, training_features: Sequence[RegimeFeatures]) -> None:
        """Fit only on an explicit training period; callers classify later rows separately."""
        training_features = tuple(training_features)
        _validate_training_features(training_features, self.config)
        matrix = _feature_matrix(training_features)
        self._scaler = StandardScaler().fit(matrix)
        scaled = self._scaler.transform(matrix)
        self._model = _build_model(self.config)
        assignments = self._model.fit_predict(scaled)
        self._cluster_labels = _descriptive_cluster_labels(assignments, training_features)
        self._hdbscan_centers = (
            _cluster_centers(assignments, scaled)
            if self.config.method is RegimeMethod.HDBSCAN
            else None
        )
        self._volatility_threshold = float(np.median(matrix[:, FEATURE_NAMES.index("volatility")]))

    def classify(self, features: Sequence[RegimeFeatures]) -> tuple[RegimeClassification, ...]:
        """Classify supplied point-in-time inputs using only the already-fitted model state."""
        if (
            self._scaler is None
            or self._model is None
            or self._cluster_labels is None
            or self._volatility_threshold is None
        ):
            raise RegimeDetectionError("regime detector must be fitted before classification")
        features = tuple(features)
        matrix = _feature_matrix(features)
        assignments, strengths = _predict(
            self._model, self._scaler.transform(matrix), self._hdbscan_centers
        )
        membership_strengths = [None] * len(features) if strengths is None else strengths
        return tuple(
            RegimeClassification(
                timestamp=feature.timestamp,
                market_regime=self._cluster_labels.get(int(assignment), MarketRegime.UNCLASSIFIED),
                volatility_regime=(
                    VolatilityRegime.HIGH
                    if feature.volatility >= self._volatility_threshold
                    else VolatilityRegime.LOW
                ),
                cluster_id=None if assignment < 0 else int(assignment),
                membership_strength=None if strength is None else float(strength),
            )
            for feature, assignment, strength in zip(
                features, assignments, membership_strengths, strict=True
            )
        )


def _validate_training_features(
    features: Sequence[RegimeFeatures], config: RegimeModelConfig
) -> None:
    if not features:
        raise RegimeDetectionError("at least one training regime feature is required")
    minimum = (
        config.min_cluster_size if config.method is RegimeMethod.HDBSCAN else config.cluster_count
    )
    if len(features) < minimum:
        raise RegimeDetectionError(f"at least {minimum} training regime features are required")
    if any(
        current.timestamp <= previous.timestamp
        for previous, current in zip(features, features[1:], strict=False)
    ):
        raise RegimeDetectionError(
            "training regime features must be in strictly increasing timestamp order"
        )


def _feature_matrix(features: Sequence[RegimeFeatures]) -> np.ndarray:
    return np.array([[getattr(feature, name) for name in FEATURE_NAMES] for feature in features])


def _build_model(config: RegimeModelConfig) -> KMeans | GaussianMixture | HDBSCAN:
    if config.method is RegimeMethod.KMEANS:
        return KMeans(n_clusters=config.cluster_count, n_init=10, random_state=config.random_seed)
    if config.method is RegimeMethod.GAUSSIAN_MIXTURE:
        return GaussianMixture(n_components=config.cluster_count, random_state=config.random_seed)
    return HDBSCAN(
        min_cluster_size=config.min_cluster_size,
        copy=False,
    )


def _descriptive_cluster_labels(
    assignments: np.ndarray,
    features: Sequence[RegimeFeatures],
) -> dict[int, MarketRegime]:
    cluster_trends: dict[int, list[float]] = {}
    for assignment, feature in zip(assignments, features, strict=True):
        if assignment >= 0:
            cluster_trends.setdefault(int(assignment), []).append(feature.trend)
    ordered_clusters = sorted(
        cluster_trends,
        key=lambda cluster_id: (
            sum(cluster_trends[cluster_id]) / len(cluster_trends[cluster_id]),
            cluster_id,
        ),
    )
    if len(ordered_clusters) < 3:
        return {cluster_id: MarketRegime.SIDEWAYS for cluster_id in ordered_clusters}
    labels = {cluster_id: MarketRegime.SIDEWAYS for cluster_id in ordered_clusters}
    labels[ordered_clusters[0]] = MarketRegime.BEAR
    labels[ordered_clusters[-1]] = MarketRegime.BULL
    return labels


def _cluster_centers(assignments: np.ndarray, scaled_features: np.ndarray) -> dict[int, np.ndarray]:
    return {
        int(cluster_id): scaled_features[assignments == cluster_id].mean(axis=0)
        for cluster_id in np.unique(assignments)
        if cluster_id >= 0
    }


def _predict(
    model: KMeans | GaussianMixture | HDBSCAN,
    scaled_features: np.ndarray,
    hdbscan_centers: dict[int, np.ndarray] | None,
) -> tuple[np.ndarray, np.ndarray | None]:
    if isinstance(model, HDBSCAN):
        if not hdbscan_centers:
            return np.full(len(scaled_features), -1), None
        cluster_ids = tuple(sorted(hdbscan_centers))
        centers = np.array([hdbscan_centers[cluster_id] for cluster_id in cluster_ids])
        closest = np.linalg.norm(scaled_features[:, np.newaxis] - centers, axis=2).argmin(axis=1)
        return np.array([cluster_ids[index] for index in closest]), None
    return model.predict(scaled_features), None
