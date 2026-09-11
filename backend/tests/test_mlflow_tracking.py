from pathlib import Path

from app.models.dataset import DatasetMetadata
from app.models.metrics import BinaryClassificationMetrics
from app.models.service_types import BaselineRunResult, FoldResult
from app.models.tracking import MlflowTracker


def test_mlflow_tracker_records_metrics_and_a_result_artifact(tmp_path: Path) -> None:
    tracker = MlflowTracker(
        f"sqlite:///{tmp_path / 'mlflow.db'}",
        (tmp_path / "artifacts").as_uri(),
        "test-baselines",
    )
    result = BaselineRunResult(
        model_name="random",
        model_version="baselines-v1",
        parameters={"random_state": 42},
        row_count=10,
        folds=(
            FoldResult(
                number=1,
                train_rows=6,
                test_rows=3,
                metrics=BinaryClassificationMetrics(0.5, 0.5, 0.5, 0.5, 0.5),
            ),
        ),
        average_metrics={
            "accuracy": 0.5,
            "precision": 0.5,
            "recall": 0.5,
            "f1": 0.5,
            "roc_auc": 0.5,
        },
    )
    metadata = DatasetMetadata("dataset-v1", "features-v1", "targets-v1", "alpaca:iex:raw", "1D")

    tracker.log(result, metadata)

    assert list((tmp_path / "artifacts").rglob("baseline_result.json"))
