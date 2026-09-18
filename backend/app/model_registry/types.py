import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum


class ModelState(StrEnum):
    CANDIDATE = "candidate"
    STAGING = "staging"
    PRODUCTION = "production"
    RETIRED = "retired"


@dataclass(frozen=True)
class ModelRegistration:
    """Immutable provenance and evidence required before a model receives a lifecycle state."""

    model_name: str
    model_version: str
    model_family: str
    dataset_version: str
    feature_version: str
    target_version: str
    parameters: Mapping[str, object]
    metrics: Mapping[str, object]
    backtest_results: Mapping[str, object]
    artifact_uri: str

    def __post_init__(self) -> None:
        for field_name in (
            "model_name",
            "model_version",
            "model_family",
            "dataset_version",
            "feature_version",
            "target_version",
            "artifact_uri",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must not be blank")
            object.__setattr__(self, field_name, value.strip())
        object.__setattr__(self, "parameters", _json_object(self.parameters, "parameters"))
        object.__setattr__(self, "metrics", _nonempty_json_object(self.metrics, "metrics"))
        object.__setattr__(
            self,
            "backtest_results",
            _nonempty_json_object(self.backtest_results, "backtest_results"),
        )


@dataclass(frozen=True)
class RegisteredModel:
    """One immutable model record plus its mutable lifecycle state."""

    id: str
    registration: ModelRegistration
    state: ModelState
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("model registry id must not be blank")
        if not isinstance(self.state, ModelState):
            raise ValueError("model registry state is invalid")
        for field_name in ("created_at", "updated_at"):
            value = getattr(self, field_name)
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{field_name} must include a timezone")
            object.__setattr__(self, field_name, value.astimezone(UTC))


def _json_object(value: Mapping[str, object], field_name: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        normalized = json.loads(json.dumps(dict(value)))
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field_name} must contain JSON-compatible values") from error
    if not isinstance(normalized, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return normalized


def _nonempty_json_object(value: Mapping[str, object], field_name: str) -> dict[str, object]:
    normalized = _json_object(value, field_name)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized
