from pathlib import Path

from app.models.advanced_types import (
    AdvancedModelRunResult,
    LeaderboardEntry,
    OptimizationResult,
    OptimizationTrial,
)
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


def test_mlflow_tracker_records_advanced_artifacts_and_a_leaderboard(tmp_path: Path) -> None:
    tracker = MlflowTracker(
        f"sqlite:///{tmp_path / 'mlflow.db'}",
        (tmp_path / "artifacts").as_uri(),
        "advanced-test-baselines",
    )
    metadata = DatasetMetadata("dataset-v1", "features-v1", "targets-v1", "alpaca:iex:raw", "1D")
    advanced_result = AdvancedModelRunResult(
        model_name="random_forest",
        model_version="advanced-v1",
        row_count=10,
        optimization=OptimizationResult(
            best_parameters={"max_depth": 3},
            best_validation_roc_auc=0.5,
            trials=(OptimizationTrial(0, 0.5, {"max_depth": 3}),),
        ),
        holdout=FoldResult(
            number=3,
            train_rows=6,
            test_rows=3,
            metrics=BinaryClassificationMetrics(0.5, 0.5, 0.5, 0.5, 0.5),
        ),
        feature_importance={"feature_one": 1.0},
    )

    tracker.log_advanced(advanced_result, metadata)
    tracker.log_leaderboard(
        (LeaderboardEntry(1, "random_forest", 0.5, 0.5),),
        metadata,
        "advanced-v1",
    )

    assert list((tmp_path / "artifacts").rglob("advanced_result.json"))
    assert list((tmp_path / "artifacts").rglob("feature_importance.json"))
    assert list((tmp_path / "artifacts").rglob("leaderboard.json"))
