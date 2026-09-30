import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from math import exp, isfinite
from pathlib import Path
from urllib.parse import unquote, urlparse

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from app.models.dataset import TrainingDataset

ARTIFACT_FORMAT = "alyntiq-linear-probability-v1"


class LinearArtifactError(ValueError):
    """Raised when a linear model artifact cannot be trained, loaded, or evaluated safely."""


@dataclass(frozen=True)
class LinearProbabilityArtifact:
    model_version: str
    dataset_version: str
    feature_version: str
    target_version: str
    source: str
    timeframe: str
    trained_through: datetime
    feature_names: tuple[str, ...]
    scaler_mean: tuple[float, ...]
    scaler_scale: tuple[float, ...]
    coefficients: tuple[float, ...]
    intercept: float
    training_rows: int

    def __post_init__(self) -> None:
        for name in (
            "model_version",
            "dataset_version",
            "feature_version",
            "target_version",
            "source",
            "timeframe",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise LinearArtifactError(f"{name} must not be blank")
            object.__setattr__(self, name, value.strip())
        if self.trained_through.tzinfo is None or self.trained_through.utcoffset() is None:
            raise LinearArtifactError("trained_through must include a timezone")
        object.__setattr__(self, "trained_through", self.trained_through.astimezone(UTC))
        if not self.feature_names or len(set(self.feature_names)) != len(self.feature_names):
            raise LinearArtifactError("feature_names must be non-empty and unique")
        if self.training_rows < 2:
            raise LinearArtifactError("training_rows must be at least 2")
        expected = len(self.feature_names)
        if any(
            len(values) != expected
            for values in (self.scaler_mean, self.scaler_scale, self.coefficients)
        ):
            raise LinearArtifactError("linear artifact arrays must match feature_names")
        if any(
            not isfinite(value)
            for value in (*self.scaler_mean, *self.scaler_scale, *self.coefficients, self.intercept)
        ):
            raise LinearArtifactError("linear artifact values must be finite")
        if any(value <= 0 for value in self.scaler_scale):
            raise LinearArtifactError("scaler_scale values must be positive")

    def predict_probability(self, features: Mapping[str, float]) -> float:
        if set(features) != set(self.feature_names):
            raise LinearArtifactError(
                "inference features must exactly match the artifact feature contract"
            )
        score = self.intercept
        for name, mean, scale, coefficient in zip(
            self.feature_names, self.scaler_mean, self.scaler_scale, self.coefficients, strict=True
        ):
            value = float(features[name])
            if not isfinite(value):
                raise LinearArtifactError(f"feature {name} must be finite")
            score += ((value - mean) / scale) * coefficient
        return _sigmoid(score)

    def as_dict(self) -> dict[str, object]:
        return {
            "format": ARTIFACT_FORMAT,
            "model_version": self.model_version,
            "dataset_version": self.dataset_version,
            "feature_version": self.feature_version,
            "target_version": self.target_version,
            "source": self.source,
            "timeframe": self.timeframe,
            "trained_through": self.trained_through.isoformat(),
            "feature_names": list(self.feature_names),
            "scaler_mean": list(self.scaler_mean),
            "scaler_scale": list(self.scaler_scale),
            "coefficients": list(self.coefficients),
            "intercept": self.intercept,
            "training_rows": self.training_rows,
        }


def train_linear_artifact(
    dataset: TrainingDataset,
    *,
    model_version: str,
    trained_through: datetime,
    random_state: int = 42,
) -> LinearProbabilityArtifact:
    if trained_through.tzinfo is None or trained_through.utcoffset() is None:
        raise LinearArtifactError("trained_through must include a timezone")
    cutoff = trained_through.astimezone(UTC)
    timestamps = pd.to_datetime(dataset.timestamps, utc=True)
    selection = timestamps < cutoff
    features = dataset.features.loc[selection]
    target = dataset.target.loc[selection]
    if len(features) < 2 or target.nunique() != 2:
        raise LinearArtifactError(
            "training rows before the cutoff must contain both target classes"
        )
    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)
    classifier = LogisticRegression(max_iter=1_000, random_state=random_state)
    classifier.fit(scaled, target)
    metadata = dataset.metadata
    return LinearProbabilityArtifact(
        model_version=model_version,
        dataset_version=metadata.dataset_version,
        feature_version=metadata.feature_version,
        target_version=metadata.target_version,
        source=metadata.source,
        timeframe=metadata.timeframe,
        trained_through=cutoff,
        feature_names=tuple(str(name) for name in features.columns),
        scaler_mean=tuple(float(value) for value in scaler.mean_),
        scaler_scale=tuple(float(value) for value in scaler.scale_),
        coefficients=tuple(float(value) for value in classifier.coef_[0]),
        intercept=float(classifier.intercept_[0]),
        training_rows=len(features),
    )


def write_linear_artifact(artifact: LinearProbabilityArtifact, uri: str) -> None:
    path = _file_uri_path(uri)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact.as_dict(), sort_keys=True, indent=2), encoding="utf-8")


def load_linear_artifact(uri: str) -> LinearProbabilityArtifact:
    path = _file_uri_path(uri)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise LinearArtifactError("linear artifact could not be read as JSON") from error
    if not isinstance(data, dict) or data.get("format") != ARTIFACT_FORMAT:
        raise LinearArtifactError("unsupported linear artifact format")
    try:
        return LinearProbabilityArtifact(
            model_version=str(data["model_version"]),
            dataset_version=str(data["dataset_version"]),
            feature_version=str(data["feature_version"]),
            target_version=str(data["target_version"]),
            source=str(data["source"]),
            timeframe=str(data["timeframe"]),
            trained_through=datetime.fromisoformat(str(data["trained_through"])),
            feature_names=tuple(str(value) for value in data["feature_names"]),
            scaler_mean=tuple(float(value) for value in data["scaler_mean"]),
            scaler_scale=tuple(float(value) for value in data["scaler_scale"]),
            coefficients=tuple(float(value) for value in data["coefficients"]),
            intercept=float(data["intercept"]),
            training_rows=int(data["training_rows"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise LinearArtifactError("linear artifact fields are invalid") from error


def _file_uri_path(uri: str) -> Path:
    parsed = urlparse(uri)
    if parsed.scheme != "file" or parsed.netloc not in ("", "localhost"):
        raise LinearArtifactError("linear artifacts require a local file URI")
    path = Path(unquote(parsed.path))
    if path.suffix != ".json":
        raise LinearArtifactError("linear artifact files must use a .json suffix")
    return path


def _sigmoid(score: float) -> float:
    if score >= 0:
        return 1 / (1 + exp(-score))
    scaled = exp(score)
    return scaled / (1 + scaled)
