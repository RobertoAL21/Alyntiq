from datetime import UTC, datetime

import pandas as pd
import pytest

from app.model_artifacts.linear import (
    LinearArtifactError,
    load_linear_artifact,
    train_linear_artifact,
    write_linear_artifact,
)
from app.models.dataset import DatasetMetadata, TrainingDataset


def test_linear_artifact_round_trip_preserves_exact_feature_contract(tmp_path) -> None:
    artifact = train_linear_artifact(
        _dataset(),
        model_version="linear-v1",
        trained_through=datetime(2024, 1, 7, tzinfo=UTC),
    )
    uri = (tmp_path / "linear-v1.json").as_uri()
    write_linear_artifact(artifact, uri)

    loaded = load_linear_artifact(uri)

    assert loaded == artifact
    assert 0 <= loaded.predict_probability({"feature_one": 1.5, "feature_two": 2.0}) <= 1
    with pytest.raises(LinearArtifactError, match="exactly match"):
        loaded.predict_probability({"feature_one": 1.5})


def test_linear_artifact_excludes_rows_at_or_after_cutoff_and_requires_both_classes() -> None:
    dataset = _dataset()
    artifact = train_linear_artifact(
        dataset,
        model_version="linear-v1",
        trained_through=datetime(2024, 1, 5, tzinfo=UTC),
    )

    assert artifact.training_rows == 3
    with pytest.raises(LinearArtifactError, match="both target classes"):
        train_linear_artifact(
            dataset,
            model_version="linear-v1",
            trained_through=datetime(2024, 1, 3, tzinfo=UTC),
        )


def test_linear_artifact_rejects_non_json_uri(tmp_path) -> None:
    artifact = train_linear_artifact(
        _dataset(),
        model_version="linear-v1",
        trained_through=datetime(2024, 1, 7, tzinfo=UTC),
    )

    with pytest.raises(LinearArtifactError, match=".json"):
        write_linear_artifact(artifact, (tmp_path / "linear-v1.pkl").as_uri())


def _dataset() -> TrainingDataset:
    return TrainingDataset(
        features=pd.DataFrame(
            {
                "feature_one": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
                "feature_two": [1.0, 2.0, 1.0, 2.0, 1.0, 2.0],
            }
        ),
        target=pd.Series([False, True, False, True, False, True]),
        timestamps=pd.Series(pd.date_range("2024-01-02", periods=6, freq="D", tz="UTC")),
        metadata=DatasetMetadata(
            dataset_version="dataset-v1",
            feature_version="features-v1",
            target_version="targets-v1",
            source="alpaca:iex:raw",
            timeframe="1D",
        ),
    )
