"""Point-in-time market-regime research primitives."""

from app.regimes.calculator import RegimeFeatureCalculationError, calculate_regime_features
from app.regimes.detector import MarketRegimeDetector, RegimeDetectionError
from app.regimes.types import (
    MarketRegime,
    RegimeBar,
    RegimeClassification,
    RegimeFeatureConfig,
    RegimeFeatures,
    RegimeMethod,
    RegimeModelConfig,
    VolatilityRegime,
)

__all__ = [
    "MarketRegime",
    "MarketRegimeDetector",
    "RegimeBar",
    "RegimeClassification",
    "RegimeDetectionError",
    "RegimeFeatureCalculationError",
    "RegimeFeatureConfig",
    "RegimeFeatures",
    "RegimeMethod",
    "RegimeModelConfig",
    "VolatilityRegime",
    "calculate_regime_features",
]
