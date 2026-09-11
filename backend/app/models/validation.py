from dataclasses import dataclass

import numpy as np
import pandas as pd


class WalkForwardValidationError(ValueError):
    """Raised when chronological observations cannot support walk-forward validation."""


@dataclass(frozen=True)
class WalkForwardFold:
    """One expanding-window training set and a strictly later evaluation set."""

    number: int
    train_indices: np.ndarray
    test_indices: np.ndarray


def expanding_window_splits(
    timestamps: pd.Series,
    *,
    n_splits: int,
    gap: int = 1,
) -> list[WalkForwardFold]:
    """Return expanding, timestamp-aligned folds with a target-horizon separation gap."""
    if n_splits < 2:
        raise WalkForwardValidationError("n_splits must be at least 2")
    if gap < 1:
        raise WalkForwardValidationError("gap must be at least 1 for the next-day target")

    normalized = pd.to_datetime(timestamps, utc=True).reset_index(drop=True)
    unique_timestamps = normalized.drop_duplicates().sort_values().to_numpy()
    if len(unique_timestamps) < n_splits + 1 + gap:
        raise WalkForwardValidationError(
            "not enough unique timestamps for the requested splits and gap"
        )

    segments = np.array_split(unique_timestamps, n_splits + 1)
    folds = []
    for number in range(1, n_splits + 1):
        train_timestamps = np.concatenate(segments[:number])
        if len(train_timestamps) <= gap:
            raise WalkForwardValidationError("the requested gap leaves no training timestamps")
        train_timestamps = train_timestamps[:-gap]
        test_timestamps = segments[number]
        train_indices = np.flatnonzero(normalized.isin(train_timestamps))
        test_indices = np.flatnonzero(normalized.isin(test_timestamps))
        folds.append(WalkForwardFold(number, train_indices, test_indices))

    return folds
