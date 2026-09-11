import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.targets.constants import TARGET_VERSION_V1
from app.targets.generator import TargetGenerator
from app.targets.repository import TargetStorageResult, load_market_bars, store_market_targets

logger = logging.getLogger(__name__)


class TargetBuildError(ValueError):
    """Raised when a configured target dataset cannot be built."""


@dataclass(frozen=True)
class TargetBuildResult:
    storage: TargetStorageResult
    target_version: str


class TargetGenerationService:
    """Build and persist versioned targets from historical market bars."""

    def build(
        self,
        session: Session,
        source: str,
        timeframe: str,
        target_version: str = TARGET_VERSION_V1,
    ) -> TargetBuildResult:
        bars = load_market_bars(session, source=source, timeframe=timeframe)
        if bars.empty:
            raise TargetBuildError("no market bars found for the selected source and timeframe")

        targets = TargetGenerator().generate(bars)
        storage = store_market_targets(session, targets, target_version=target_version)
        logger.info(
            "market_targets_built",
            extra={
                "target_version": target_version,
                "source": source,
                "timeframe": timeframe,
                "received": storage.received,
                "inserted": storage.inserted,
                "skipped": storage.skipped,
            },
        )
        return TargetBuildResult(storage=storage, target_version=target_version)
