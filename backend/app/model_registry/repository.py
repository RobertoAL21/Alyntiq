from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.model_registry import ModelRegistryRecord
from app.model_registry.types import ModelRegistration, ModelState, RegisteredModel


class ModelRegistryError(ValueError):
    """Raised when persisted model lifecycle data cannot be found or would be inconsistent."""


def find_registered_model(session: Session, model_version: str) -> RegisteredModel | None:
    record = session.scalar(
        select(ModelRegistryRecord).where(
            ModelRegistryRecord.model_version == model_version.strip()
        )
    )
    return None if record is None else _to_registered_model(record)


def list_registered_models(session: Session) -> tuple[RegisteredModel, ...]:
    records = session.scalars(
        select(ModelRegistryRecord).order_by(ModelRegistryRecord.created_at, ModelRegistryRecord.id)
    )
    return tuple(_to_registered_model(record) for record in records)


def store_registered_model(session: Session, registration: ModelRegistration) -> RegisteredModel:
    record = ModelRegistryRecord(
        id=str(uuid4()),
        model_name=registration.model_name,
        model_version=registration.model_version,
        model_family=registration.model_family,
        state=ModelState.CANDIDATE.value,
        dataset_version=registration.dataset_version,
        feature_version=registration.feature_version,
        target_version=registration.target_version,
        parameters=dict(registration.parameters),
        metrics=dict(registration.metrics),
        backtest_results=dict(registration.backtest_results),
        artifact_uri=registration.artifact_uri,
    )
    session.add(record)
    session.flush()
    return _to_registered_model(record)


def update_model_state(
    session: Session,
    *,
    model_version: str,
    state: ModelState,
    updated_at: datetime,
) -> RegisteredModel:
    record = _require_record(session, model_version)
    record.state = state.value
    record.updated_at = updated_at.astimezone(UTC)
    session.flush()
    return _to_registered_model(record)


def _require_record(session: Session, model_version: str) -> ModelRegistryRecord:
    record = session.scalar(
        select(ModelRegistryRecord).where(
            ModelRegistryRecord.model_version == model_version.strip()
        )
    )
    if record is None:
        raise ModelRegistryError(f"model version is not registered: {model_version}")
    return record


def _to_registered_model(record: ModelRegistryRecord) -> RegisteredModel:
    return RegisteredModel(
        id=record.id,
        registration=ModelRegistration(
            model_name=record.model_name,
            model_version=record.model_version,
            model_family=record.model_family,
            dataset_version=record.dataset_version,
            feature_version=record.feature_version,
            target_version=record.target_version,
            parameters=record.parameters,
            metrics=record.metrics,
            backtest_results=record.backtest_results,
            artifact_uri=record.artifact_uri,
        ),
        state=ModelState(record.state),
        created_at=_as_utc(record.created_at),
        updated_at=_as_utc(record.updated_at),
    )


def _as_utc(timestamp: datetime) -> datetime:
    return timestamp.replace(tzinfo=UTC) if timestamp.tzinfo is None else timestamp.astimezone(UTC)
