from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from app.regimes.types import MarketRegime


class DriftKind(StrEnum):
    """The independent signals evaluated by the drift detector."""

    FEATURE = "feature"
    PREDICTION = "prediction"
    VOLATILITY = "volatility"
    MARKET_REGIME = "market_regime"


@dataclass(frozen=True)
class DriftConfig:
    """Thresholds for comparing a fixed reference sample with a later sample."""

    distribution_bins: int = 10
    feature_psi_threshold: float = 0.2
    prediction_psi_threshold: float = 0.2
    volatility_relative_change_threshold: float = 0.3

    def __post_init__(self) -> None:
        if self.distribution_bins < 2:
            raise ValueError("distribution_bins must be at least 2")
        for name in (
            "feature_psi_threshold",
            "prediction_psi_threshold",
            "volatility_relative_change_threshold",
        ):
            value = getattr(self, name)
            if not isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be a finite value greater than zero")


@dataclass(frozen=True)
class DistributionDrift:
    """Population stability comparison for one numeric input distribution."""

    name: str
    population_stability_index: float
    reference_mean: float
    current_mean: float
    drifted: bool


@dataclass(frozen=True)
class VolatilityDrift:
    """Relative change in mean trailing volatility across two periods."""

    reference_mean: float
    current_mean: float
    relative_change: float
    drifted: bool


@dataclass(frozen=True)
class MarketRegimeDrift:
    """Change in the dominant descriptive regime between two samples."""

    reference_regime: MarketRegime
    current_regime: MarketRegime
    changed: bool


@dataclass(frozen=True)
class DriftAlert:
    """A local, structured alert; delivery is deliberately outside this phase."""

    kind: DriftKind
    subject: str
    value: float | str
    threshold: float | str


@dataclass(frozen=True)
class DriftReport:
    """All comparisons and alerts generated for one reference/current evaluation."""

    feature_distributions: tuple[DistributionDrift, ...]
    prediction_distribution: DistributionDrift | None
    volatility: VolatilityDrift | None
    market_regime: MarketRegimeDrift | None
    alerts: tuple[DriftAlert, ...]
