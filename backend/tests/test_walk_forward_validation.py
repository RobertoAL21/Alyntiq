import pandas as pd
import pytest

from app.models.validation import WalkForwardValidationError, expanding_window_splits


def test_expanding_windows_are_chronological_and_respect_the_target_gap() -> None:
    timestamps = pd.Series(
        timestamp
        for timestamp in pd.date_range("2024-01-02", periods=12, freq="B", tz="UTC")
        for _ in range(2)
    )

    folds = expanding_window_splits(timestamps, n_splits=3, gap=1)

    assert len(folds) == 3
    for fold in folds:
        train_timestamps = timestamps.iloc[fold.train_indices]
        test_timestamps = timestamps.iloc[fold.test_indices]
        assert train_timestamps.max() < test_timestamps.min()
        assert (test_timestamps.min() - train_timestamps.max()).days >= 2


def test_rejects_a_validation_configuration_without_a_next_day_gap() -> None:
    timestamps = pd.Series(pd.date_range("2024-01-02", periods=12, freq="B", tz="UTC"))

    with pytest.raises(WalkForwardValidationError, match="gap"):
        expanding_window_splits(timestamps, n_splits=2, gap=0)
