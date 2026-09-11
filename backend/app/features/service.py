import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.features.calculator import calculate_features
from app.features.constants import FEATURE_VERSION_V1, MARKET_CONTEXT_SYMBOLS
from app.features.repository import FeatureStorageResult, load_market_bars, store_market_features

logger = logging.getLogger(__name__)


class FeatureBuildError(ValueError):
    """Raised when the feature dataset cannot satisfy the configured feature contract."""


@dataclass(frozen=True)
class FeatureBuildResult:
    storage: FeatureStorageResult
    feature_version: str


class FeatureEngineeringService:
    """Build and persist versioned, point-in-time features from historical bars."""

    def build(
        self,
        session: Session,
        source: str,
        timeframe: str,
        feature_version: str = FEATURE_VERSION_V1,
    ) -> FeatureBuildResult:
        bars = load_market_bars(session, source=source, timeframe=timeframe)
        available_symbols = set(bars["symbol"])
        missing_context = MARKET_CONTEXT_SYMBOLS.difference(available_symbols)
        if missing_context:
            missing = ", ".join(sorted(missing_context))
            raise FeatureBuildError(f"market context bars are missing for: {missing}")

        features = calculate_features(bars)
        storage = store_market_features(session, features, feature_version=feature_version)
        logger.info(
            "market_features_built",
            extra={
                "feature_version": feature_version,
                "source": source,
                "timeframe": timeframe,
                "received": storage.received,
                "inserted": storage.inserted,
                "skipped": storage.skipped,
            },
        )
        return FeatureBuildResult(storage=storage, feature_version=feature_version)
