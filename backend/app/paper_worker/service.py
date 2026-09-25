import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.paper_worker.repository import store_preflight
from app.paper_worker.types import PaperWorkerPreflight, PaperWorkerPreflightOutcome
from app.strategy_deployments.service import StrategyDeploymentError, StrategyDeploymentService
from app.strategy_deployments.types import StrategyDeploymentState

logger = logging.getLogger(__name__)


class PaperWorkerService:
    """Run one non-executing runtime preflight for currently armed deployments."""

    def __init__(self, deployments: StrategyDeploymentService | None = None) -> None:
        self._deployments = deployments or StrategyDeploymentService()

    def run_once(
        self, session: Session, *, settings: Settings, now: datetime | None = None
    ) -> tuple[PaperWorkerPreflight, ...]:
        checked_at = _now(now)
        results = []
        for deployment in self._deployments.list(session):
            if deployment.state is not StrategyDeploymentState.ARMED:
                continue
            try:
                self._deployments.assert_eligible(session, deployment, settings)
                outcome = PaperWorkerPreflightOutcome.READY
                reason = "armed paper deployment remains eligible for a future runtime"
            except StrategyDeploymentError as error:
                outcome = PaperWorkerPreflightOutcome.BLOCKED
                reason = str(error)
            preflight = store_preflight(
                session,
                PaperWorkerPreflight(
                    deployment_id=deployment.id,
                    outcome=outcome,
                    reason=reason,
                    checked_at=checked_at,
                ),
            )
            logger.info(
                "paper_worker_preflight_completed",
                extra={
                    "deployment_id": deployment.id,
                    "outcome": preflight.outcome.value,
                    "model_version": deployment.spec.model_version,
                },
            )
            results.append(preflight)
        return tuple(results)


def _now(value: datetime | None) -> datetime:
    timestamp = datetime.now(UTC) if value is None else value
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("worker timestamps must include a timezone")
    return timestamp.astimezone(UTC)
