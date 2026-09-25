from datetime import UTC

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.paper_worker_preflight import PaperWorkerPreflightRecord
from app.paper_worker.types import PaperWorkerPreflight, PaperWorkerPreflightOutcome


def store_preflight(session: Session, preflight: PaperWorkerPreflight) -> PaperWorkerPreflight:
    session.add(
        PaperWorkerPreflightRecord(
            id=preflight.id,
            deployment_id=preflight.deployment_id,
            outcome=preflight.outcome.value,
            reason=preflight.reason,
            checked_at=preflight.checked_at,
        )
    )
    session.flush()
    return preflight


def latest_preflights_by_deployment(
    session: Session, deployment_ids: tuple[str, ...]
) -> dict[str, PaperWorkerPreflight]:
    if not deployment_ids:
        return {}
    records = session.scalars(
        select(PaperWorkerPreflightRecord)
        .where(PaperWorkerPreflightRecord.deployment_id.in_(deployment_ids))
        .order_by(
            PaperWorkerPreflightRecord.deployment_id,
            PaperWorkerPreflightRecord.checked_at.desc(),
            PaperWorkerPreflightRecord.id.desc(),
        )
    )
    latest: dict[str, PaperWorkerPreflight] = {}
    for record in records:
        latest.setdefault(record.deployment_id, _to_preflight(record))
    return latest


def _to_preflight(record: PaperWorkerPreflightRecord) -> PaperWorkerPreflight:
    timestamp = record.checked_at
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    else:
        timestamp = timestamp.astimezone(UTC)
    return PaperWorkerPreflight(
        id=record.id,
        deployment_id=record.deployment_id,
        outcome=PaperWorkerPreflightOutcome(record.outcome),
        reason=record.reason,
        checked_at=timestamp,
    )
