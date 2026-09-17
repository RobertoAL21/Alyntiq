import numpy as np
import pandas as pd
import pytest

from app.models.dataset import DatasetMetadata, TrainingDataset
from app.models.deep_learning import (
    DeepLearningConfig,
    DeepLearningError,
    build_temporal_sequences,
    deep_learning_model_definitions,
)
from app.models.deep_learning_service import DeepLearningExperimentService


class RecordedDeepLearningTracker:
    def __init__(self) -> None:
        self.model_names: list[str] = []
        self.leaderboard_recorded = False

    def log_deep_learning(self, result, metadata, config) -> None:
        self.model_names.append(result.model_name)

    def log_deep_learning_leaderboard(self, leaderboard, metadata, model_version) -> None:
        self.leaderboard_recorded = True


def make_dataset(rows_per_symbol: int = 28) -> TrainingDataset:
    timestamps = pd.date_range("2024-01-02", periods=rows_per_symbol, freq="B", tz="UTC")
    features = []
    targets = []
    row_timestamps = []
    symbols = []
    for symbol, offset in (("AAPL", 0.0), ("MSFT", 100.0)):
        for index, value in enumerate(range(rows_per_symbol)):
            features.append({"feature_one": offset + value, "feature_two": float(value % 3)})
            targets.append(bool(value % 2))
            row_timestamps.append(timestamps[index])
            symbols.append(symbol)
    return TrainingDataset(
        features=pd.DataFrame(features),
        target=pd.Series(targets),
        timestamps=pd.Series(row_timestamps),
        metadata=DatasetMetadata("dataset-v1", "features-v1", "targets-v1", "alpaca:iex:raw", "1D"),
        symbols=pd.Series(symbols),
    )


def test_temporal_sequences_are_symbol_local_and_end_at_the_target_timestamp() -> None:
    dataset = make_dataset(rows_per_symbol=6)

    sequences = build_temporal_sequences(dataset, lookback=3)

    assert sequences.sequences.shape == (8, 3, 2)
    assert sequences.timestamps.iloc[0] == dataset.timestamps.iloc[2]
    assert np.all(sequences.sequences[:4, :, 0] < 100)
    assert np.all(sequences.sequences[4:, :, 0] >= 100)


def test_temporal_sequences_require_symbol_identity() -> None:
    dataset = make_dataset(rows_per_symbol=6)
    without_symbols = TrainingDataset(
        features=dataset.features,
        target=dataset.target,
        timestamps=dataset.timestamps,
        metadata=dataset.metadata,
    )

    with pytest.raises(DeepLearningError, match="requires a symbol"):
        build_temporal_sequences(without_symbols, lookback=3)


def test_deep_learning_experiment_evaluates_all_initial_architectures_on_reserved_holdout() -> None:
    config = DeepLearningConfig(lookback=4, hidden_size=4, epochs=1, batch_size=16)
    result = DeepLearningExperimentService().run(make_dataset(), config=config, n_splits=3, gap=1)

    assert [definition.name for definition in deep_learning_model_definitions()] == [
        "lstm",
        "gru",
        "temporal_cnn",
        "transformer",
    ]
    assert [run.model_name for run in result.runs] == [
        "lstm",
        "gru",
        "temporal_cnn",
        "transformer",
        "baseline_random",
        "baseline_majority_class",
        "baseline_logistic_regression",
        "baseline_decision_tree",
    ]
    assert [run.model_family for run in result.runs] == [
        "deep_learning",
        "deep_learning",
        "deep_learning",
        "deep_learning",
        "baseline",
        "baseline",
        "baseline",
        "baseline",
    ]
    assert all(run.holdout.number == 3 for run in result.runs)
    assert all(len(run.validation_folds) == 2 for run in result.runs)
    assert {entry.model_name for entry in result.leaderboard} == {
        "lstm",
        "gru",
        "temporal_cnn",
        "transformer",
        "baseline_random",
        "baseline_majority_class",
        "baseline_logistic_regression",
        "baseline_decision_tree",
    }


def test_deep_learning_experiment_tracks_each_model_and_its_leaderboard() -> None:
    tracker = RecordedDeepLearningTracker()
    config = DeepLearningConfig(lookback=4, hidden_size=4, epochs=1, batch_size=16)

    DeepLearningExperimentService(tracker).run(make_dataset(), config=config, n_splits=3, gap=1)

    assert tracker.model_names == [
        "lstm",
        "gru",
        "temporal_cnn",
        "transformer",
        "baseline_random",
        "baseline_majority_class",
        "baseline_logistic_regression",
        "baseline_decision_tree",
    ]
    assert tracker.leaderboard_recorded is True
