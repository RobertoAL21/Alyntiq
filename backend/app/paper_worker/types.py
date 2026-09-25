from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class PaperWorkerPreflightOutcome(StrEnum):
    READY = "ready"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class PaperWorkerPreflight:
    """Immutable result of checking one armed deployment at a point in time."""

    deployment_id: str
    outcome: PaperWorkerPreflightOutcome
    reason: str
    checked_at: datetime
    id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        for field_name in ("id", "deployment_id"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must not be blank")
        try:
            UUID(self.id)
        except ValueError as error:
            raise ValueError("preflight id must be a UUID") from error
        if not isinstance(self.outcome, PaperWorkerPreflightOutcome):
            raise ValueError("preflight outcome is invalid")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("preflight reason must not be blank")
        if len(self.reason.strip()) > 512:
            raise ValueError("preflight reason is too long")
        if self.checked_at.tzinfo is None or self.checked_at.utcoffset() is None:
            raise ValueError("preflight checked_at must include a timezone")
        object.__setattr__(self, "deployment_id", self.deployment_id.strip())
        object.__setattr__(self, "reason", self.reason.strip())
        object.__setattr__(self, "checked_at", self.checked_at.astimezone(UTC))
