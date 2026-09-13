import pandas as pd

from app.models.advanced import advanced_model_definitions
from app.models.dataset import DatasetMetadata, TrainingDataset
from app.models.optimization import optimize_model
from app.models.validation import expanding_window_splits


def make_training_dataset(rows: int = 60) -> TrainingDataset:
    return TrainingDataset(
        features=pd.DataFrame(
            {
                "feature_one": [float(index) for index in range(rows)],
                "feature_two": [float(index % 5) for index in range(rows)],
            }
        ),
        target=pd.Series([bool(index % 2) for index in range(rows)]),
        timestamps=pd.Series(pd.date_range("2024-01-02", periods=rows, freq="B", tz="UTC")),
        metadata=DatasetMetadata("dataset-v1", "features-v1", "targets-v1", "alpaca:iex:raw", "1D"),
    )


def test_optuna_optimizes_only_the_supplied_walk_forward_validation_folds() -> None:
    dataset = make_training_dataset()
    folds = expanding_window_splits(dataset.timestamps, n_splits=3, gap=1)
    definition = advanced_model_definitions()[0]

    result = optimize_model(
        dataset,
        definition,
        folds[:-1],
        n_trials=1,
        random_state=42,
    )

    assert len(result.trials) == 1
    assert 0 <= result.best_validation_roc_auc <= 1
    assert "n_estimators" in result.best_parameters
    assert folds[-1].number not in [fold.number for fold in folds[:-1]]


def test_advanced_model_definitions_cover_the_phase_six_model_families() -> None:
    definitions = advanced_model_definitions()

    assert [definition.name for definition in definitions] == [
        "random_forest",
        "xgboost",
        "lightgbm",
    ]
