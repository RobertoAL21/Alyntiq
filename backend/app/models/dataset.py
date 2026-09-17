from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class DatasetMetadata:
    """Versioned lineage required to reproduce a baseline-model experiment."""

    dataset_version: str
    feature_version: str
    target_version: str
    source: str
    timeframe: str


@dataclass(frozen=True)
class TrainingDataset:
    """Chronological model inputs and labels kept in separate data structures."""

    features: pd.DataFrame
    target: pd.Series
    timestamps: pd.Series
    metadata: DatasetMetadata
    symbols: pd.Series | None = None

    def __post_init__(self) -> None:
        if len(self.features) != len(self.target) or len(self.target) != len(self.timestamps):
            raise ValueError("features, target, and timestamps must have equal lengths")
        if self.target.isna().any():
            raise ValueError("training targets must not contain null values")
        if self.symbols is not None and len(self.symbols) != len(self.features):
            raise ValueError("symbols must have the same length as features")

    @property
    def row_count(self) -> int:
        return len(self.features)
