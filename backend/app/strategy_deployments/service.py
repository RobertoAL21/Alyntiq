import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.model_registry.service import ModelLifecycleError, ModelRegistryService
from app.strategy_deployments.repository import (
    StrategyDeploymentRepositoryError,
    find_deployment,
    list_deployments,
    store_deployment,
    update_deployment_state,
)
from app.strategy_deployments.types import (
    StrategyDeployment,
    StrategyDeploymentSpec,
    StrategyDeploymentState,
)


class StrategyDeploymentError(ValueError):
    """Raised when a paper deployment cannot be created or transitioned safely."""


logger = logging.getLogger(__name__)


class StrategyDeploymentService:
    """Control plane for configuration only; it never starts a worker or submits an order."""

    def __init__(self, registry: ModelRegistryService | None = None) -> None:
        self._registry = registry or ModelRegistryService()

    def list(self, session: Session) -> tuple[StrategyDeployment, ...]:
        return list_deployments(session)

    def create(self, session: Session, spec: StrategyDeploymentSpec) -> StrategyDeployment:
        try:
            self._registry.get(session, spec.model_version)
        except ModelLifecycleError as error:
            raise StrategyDeploymentError(str(error)) from error
        deployment = store_deployment(session, spec)
        logger.info(
            "strategy_deployment_created",
            extra={"deployment_id": deployment.id, "model_version": spec.model_version},
        )
        return deployment

    def validate(
        self,
        session: Session,
        *,
        deployment_id: str,
        settings: Settings,
        now: datetime | None = None,
    ) -> StrategyDeployment:
        deployment = self._get(session, deployment_id)
        if deployment.state is StrategyDeploymentState.ARMED:
            raise StrategyDeploymentError("disarm the deployment before validating it again")
        self._assert_eligible(session, deployment, settings)
        if deployment.state is StrategyDeploymentState.VALIDATED:
            return deployment
        updated = update_deployment_state(
            session,
            deployment_id=deployment.id,
            state=StrategyDeploymentState.VALIDATED,
            updated_at=_now(now),
        )
        logger.info("strategy_deployment_validated", extra={"deployment_id": updated.id})
        return updated

    def arm(
        self,
        session: Session,
        *,
        deployment_id: str,
        settings: Settings,
        now: datetime | None = None,
    ) -> StrategyDeployment:
        deployment = self._get(session, deployment_id)
        if deployment.state is StrategyDeploymentState.ARMED:
            self._assert_eligible(session, deployment, settings)
            return deployment
        if deployment.state is not StrategyDeploymentState.VALIDATED:
            raise StrategyDeploymentError("only a validated deployment can be armed")
        self._assert_eligible(session, deployment, settings)
        updated = update_deployment_state(
            session,
            deployment_id=deployment.id,
            state=StrategyDeploymentState.ARMED,
            updated_at=_now(now),
        )
        logger.info("strategy_deployment_armed", extra={"deployment_id": updated.id})
        return updated

    def disarm(
        self,
        session: Session,
        *,
        deployment_id: str,
        now: datetime | None = None,
    ) -> StrategyDeployment:
        deployment = self._get(session, deployment_id)
        if deployment.state is StrategyDeploymentState.VALIDATED:
            return deployment
        if deployment.state is not StrategyDeploymentState.ARMED:
            raise StrategyDeploymentError("only an armed deployment can be disarmed")
        updated = update_deployment_state(
            session,
            deployment_id=deployment.id,
            state=StrategyDeploymentState.VALIDATED,
            updated_at=_now(now),
        )
        logger.info("strategy_deployment_disarmed", extra={"deployment_id": updated.id})
        return updated

    def _get(self, session: Session, deployment_id: str) -> StrategyDeployment:
        try:
            deployment = find_deployment(session, deployment_id)
        except StrategyDeploymentRepositoryError as error:
            raise StrategyDeploymentError(str(error)) from error
        if deployment is None:
            raise StrategyDeploymentError(f"strategy deployment was not found: {deployment_id}")
        return deployment

    def _assert_eligible(
        self, session: Session, deployment: StrategyDeployment, settings: Settings
    ) -> None:
        if settings.trading_environment != "paper":
            raise StrategyDeploymentError("paper deployments require TRADING_ENVIRONMENT=paper")
        try:
            model = self._registry.require_paper_trading_eligibility(
                session, deployment.spec.model_version
            )
        except ModelLifecycleError as error:
            raise StrategyDeploymentError(str(error)) from error
        registration = model.registration
        if registration.feature_version != deployment.spec.feature_version:
            raise StrategyDeploymentError(
                "deployment feature_version does not match the registered model"
            )
        if registration.target_version != deployment.spec.target_version:
            raise StrategyDeploymentError(
                "deployment target_version does not match the registered model"
            )


def _now(value: datetime | None) -> datetime:
    now = datetime.now(UTC) if value is None else value
    if now.tzinfo is None or now.utcoffset() is None:
        raise StrategyDeploymentError("transition timestamps must include a timezone")
    return now.astimezone(UTC)
