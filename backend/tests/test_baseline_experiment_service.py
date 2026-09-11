import pandas as pd

from app.models.baselines import baseline_definitions
from app.models.dataset import DatasetMetadata, TrainingDataset
from app.models.service import BaselineExperimentService
from app.models.validation import expanding_window_splits


class RecordedTracker:
    def __init__(self) -> None:
        self.records = []

    def log(self, result, metadata) -> None:
        self.records.append((result, metadata))


def test_evaluates_all_baselines_with_reproducible_walk_forward_folds() -> None:
    rows = 24
    timestamps = pd.Series(pd.date_range("2024-01-02", periods=rows, freq="B", tz="UTC"))
    dataset = TrainingDataset(
        features=pd.DataFrame(
            {
                "feature_one": [float(index) for index in range(rows)],
                "feature_two": [float(index % 3) for index in range(rows)],
            }
        ),
        target=pd.Series([bool(index % 2) for index in range(rows)]),
        timestamps=timestamps,
        metadata=DatasetMetadata(
            dataset_version="dataset-v1",
            feature_version="features-v1",
            target_version="targets-v1",
            source="alpaca:iex:raw",
            timeframe="1D",
        ),
    )
    tracker = RecordedTracker()
    service = BaselineExperimentService(tracker)
    folds = expanding_window_splits(timestamps, n_splits=2, gap=1)

    runs = tuple(
        service._run_definition(
            dataset,
            definition,
            folds=folds,
            random_state=42,
            model_version="baselines-v1",
        )
        for definition in baseline_definitions()
    )
    for run in runs:
        tracker.log(run, dataset.metadata)

    assert [run.model_name for run in runs] == [
        "random",
        "majority_class",
        "logistic_regression",
        "decision_tree",
    ]
    assert all(len(run.folds) == 2 for run in runs)
    assert all(
        set(run.average_metrics) == {"accuracy", "precision", "recall", "f1", "roc_auc"}
        for run in runs
    )
    assert len(tracker.records) == 4
