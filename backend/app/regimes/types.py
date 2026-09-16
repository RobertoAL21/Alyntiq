from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from math import isfinite


class RegimeMethod(StrEnum):
    KMEANS = "kmeans"
    GAUSSIAN_MIXTURE = "gaussian_mixture"
    HDBSCAN = "hdbscan"


class MarketRegime(StrEnum):
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    UNCLASSIFIED = "unclassified"


class VolatilityRegime(StrEnum):
    HIGH = "high_volatility"
    LOW = "low_volatility"


@dataclass(frozen=True)
class RegimeBar:
    """One completed daily bar used to calculate trailing market-regime features."""

    timestamp: datetime
    symbol: str
    close: float
    volume: float

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("regime bar timestamps must include a timezone")
        if not self.symbol.strip():
            raise ValueError("regime bar symbol must not be blank")
        if not isfinite(self.close) or self.close <= 0:
            raise ValueError("regime bar close must be a finite positive value")
        if not isfinite(self.volume) or self.volume < 0:
            raise ValueError("regime bar volume must be a finite non-negative value")
        object.__setattr__(self, "timestamp", self.timestamp.astimezone(UTC))
        object.__setattr__(self, "symbol", self.symbol.strip().upper())


@dataclass(frozen=True)
class RegimeFeatureConfig:
    """Explicit market symbols and trailing-window assumptions for regime features."""

    market_symbol: str = "SPY"
    correlation_symbol: str = "QQQ"
    window: int = 20
    trading_days_per_year: int = 252

    def __post_init__(self) -> None:
        if not self.market_symbol.strip() or not self.correlation_symbol.strip():
            raise ValueError("regime feature symbols must not be blank")
        if self.market_symbol.strip().upper() == self.correlation_symbol.strip().upper():
            raise ValueError("regime feature symbols must be different")
        if self.window < 2:
            raise ValueError("regime feature window must be at least 2")
        if self.trading_days_per_year < 1:
            raise ValueError("trading_days_per_year must be at least 1")
        object.__setattr__(self, "market_symbol", self.market_symbol.strip().upper())
        object.__setattr__(self, "correlation_symbol", self.correlation_symbol.strip().upper())


@dataclass(frozen=True)
class RegimeFeatures:
    """Trailing, point-in-time market inputs for unsupervised regime research."""

    timestamp: datetime
    return_value: float
    trend: float
    volatility: float
    volume_ratio: float
    correlation: float

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("regime feature timestamps must include a timezone")
        for name in ("return_value", "trend", "volatility", "volume_ratio", "correlation"):
            if not isfinite(getattr(self, name)):
                raise ValueError(f"regime feature {name} must be finite")
        if self.volatility < 0:
            raise ValueError("regime feature volatility must not be negative")
        if self.volume_ratio < 0:
            raise ValueError("regime feature volume_ratio must not be negative")
        if not -1 <= self.correlation <= 1:
            raise ValueError("regime feature correlation must be between -1 and 1")
        object.__setattr__(self, "timestamp", self.timestamp.astimezone(UTC))


@dataclass(frozen=True)
class RegimeModelConfig:
    """Reproducible configuration for one unsupervised regime-model fit."""

    method: RegimeMethod
    cluster_count: int = 3
    min_cluster_size: int = 10
    random_seed: int = 42

    def __post_init__(self) -> None:
        if not isinstance(self.method, RegimeMethod):
            raise ValueError("regime method must be a supported RegimeMethod")
        if self.cluster_count < 3:
            raise ValueError("cluster_count must be at least 3 for bear, sideways, and bull labels")
        if self.min_cluster_size < 2:
            raise ValueError("min_cluster_size must be at least 2")


@dataclass(frozen=True)
class RegimeClassification:
    """A descriptive regime result from a model fitted on an earlier explicit period."""

    timestamp: datetime
    market_regime: MarketRegime
    volatility_regime: VolatilityRegime
    cluster_id: int | None
    membership_strength: float | None

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("regime classification timestamps must include a timezone")
        if self.cluster_id is not None and self.cluster_id < 0:
            raise ValueError("regime classification cluster_id must not be negative")
        if self.membership_strength is not None and not 0 <= self.membership_strength <= 1:
            raise ValueError("regime membership_strength must be between 0 and 1")
        object.__setattr__(self, "timestamp", self.timestamp.astimezone(UTC))
