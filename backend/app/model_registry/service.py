import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.model_registry.repository import (
    ModelRegistryError,
    find_registered_model,
    list_registered_models,
    store_registered_model,
    update_model_state,
)
from app.model_registry.types import ModelRegistration, ModelState, RegisteredModel


class ModelLifecycleError(ValueError):
    """Raised when a model lifecycle transition or paper-trading gate is not allowed."""


_ALLOWED_TRANSITIONS: dict[ModelState, frozenset[ModelState]] = {
    ModelState.CANDIDATE: frozenset({ModelState.STAGING, ModelState.RETIRED}),
    ModelState.STAGING: frozenset(
        {ModelState.CANDIDATE, ModelState.PRODUCTION, ModelState.RETIRED}
    ),
    ModelState.PRODUCTION: frozenset({ModelState.STAGING, ModelState.RETIRED}),
    ModelState.RETIRED: frozenset(),
}

logger = logging.getLogger(__name__)


class ModelRegistryService:
    """Manage explicit model promotion without coupling registry state to model training."""

    def register(self, session: Session, registration: ModelRegistration) -> RegisteredModel:
        existing = find_registered_model(session, registration.model_version)
        if existing is None:
            model = store_registered_model(session, registration)
            logger.info(
                "model_registered",
                extra={
                    "model_version": registration.model_version,
                    "model_family": registration.model_family,
                    "state": model.state.value,
                },
            )
            return model
        if existing.registration != registration:
            raise ModelLifecycleError(
                "model version is already registered with different provenance or evidence"
            )
        return existing

    def list(self, session: Session) -> tuple[RegisteredModel, ...]:
        return list_registered_models(session)

    def transition(
        self,
        session: Session,
        *,
        model_version: str,
        target_state: ModelState,
        now: datetime | None = None,
    ) -> RegisteredModel:
        try:
            current = self.get(session, model_version)
        except ModelRegistryError as error:
            raise ModelLifecycleError(str(error)) from error
        if current.state is target_state:
            return current
        if target_state not in _ALLOWED_TRANSITIONS[current.state]:
            raise ModelLifecycleError(
                f"cannot transition model from {current.state.value} to {target_state.value}"
            )
        if now is not None and (now.tzinfo is None or now.utcoffset() is None):
            raise ModelLifecycleError("transition timestamps must include a timezone")
        model = update_model_state(
            session,
            model_version=model_version,
            state=target_state,
            updated_at=datetime.now(UTC) if now is None else now,
        )
        logger.info(
            "model_state_transitioned",
            extra={
                "model_version": model.registration.model_version,
                "previous_state": current.state.value,
                "state": model.state.value,
            },
        )
        return model

    def get(self, session: Session, model_version: str) -> RegisteredModel:
        try:
            model = find_registered_model(session, model_version)
        except AttributeError as error:
            raise ModelLifecycleError("model_version must be a non-blank string") from error
        if model is None:
            raise ModelLifecycleError(f"model version is not registered: {model_version}")
        return model

    def require_paper_trading_eligibility(
        self, session: Session, model_version: str
    ) -> RegisteredModel:
        model = self.get(session, model_version)
        if model.state is not ModelState.PRODUCTION:
            raise ModelLifecycleError(
                f"model version {model.registration.model_version} is not production"
            )
        return model
