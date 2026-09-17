from collections.abc import Callable
from dataclasses import dataclass
from math import isfinite

import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import StandardScaler
from torch import Tensor, nn

from app.models.dataset import TrainingDataset


class DeepLearningError(ValueError):
    """Raised when time-series sequences or neural-model settings are invalid."""


@dataclass(frozen=True)
class DeepLearningConfig:
    """Fixed, reproducible CPU training settings for a temporal binary classifier."""

    lookback: int = 20
    hidden_size: int = 16
    epochs: int = 10
    batch_size: int = 32
    learning_rate: float = 0.001
    random_state: int = 42

    def __post_init__(self) -> None:
        if self.lookback < 2:
            raise DeepLearningError("lookback must be at least 2")
        if self.hidden_size < 2:
            raise DeepLearningError("hidden_size must be at least 2")
        if self.hidden_size % 2:
            raise DeepLearningError("hidden_size must be even for the Transformer attention heads")
        if self.epochs < 1 or self.batch_size < 1:
            raise DeepLearningError("epochs and batch_size must be positive")
        if not isfinite(self.learning_rate) or self.learning_rate <= 0:
            raise DeepLearningError("learning_rate must be finite and positive")


@dataclass(frozen=True)
class TemporalSequenceDataset:
    """Symbol-local trailing feature windows with the target at each window end."""

    sequences: np.ndarray
    targets: np.ndarray
    timestamps: pd.Series
    feature_names: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.sequences.ndim != 3:
            raise DeepLearningError("temporal sequences must be three-dimensional")
        if len(self.sequences) != len(self.targets) or len(self.targets) != len(self.timestamps):
            raise DeepLearningError("temporal sequences, targets, and timestamps must align")
        if self.sequences.shape[2] != len(self.feature_names):
            raise DeepLearningError("temporal feature names must match sequence width")
        if not len(self.sequences):
            raise DeepLearningError("at least one temporal sequence is required")


@dataclass(frozen=True)
class DeepLearningModelDefinition:
    name: str
    factory: Callable[[int, DeepLearningConfig], nn.Module]


def build_temporal_sequences(
    dataset: TrainingDataset,
    *,
    lookback: int,
) -> TemporalSequenceDataset:
    """Create per-symbol trailing windows ending at the point-in-time feature row."""
    if dataset.symbols is None:
        raise DeepLearningError("temporal learning requires a symbol for every training row")
    if lookback < 2:
        raise DeepLearningError("lookback must be at least 2")

    frame = dataset.features.copy()
    frame["_target"] = dataset.target.to_numpy(dtype=bool)
    frame["_timestamp"] = pd.to_datetime(dataset.timestamps, utc=True).to_numpy()
    frame["_symbol"] = dataset.symbols.astype(str).str.strip().str.upper().to_numpy()
    windows: list[np.ndarray] = []
    targets: list[bool] = []
    timestamps: list[pd.Timestamp] = []
    for _, group in frame.sort_values(["_symbol", "_timestamp"]).groupby("_symbol"):
        values = group.loc[:, dataset.features.columns].to_numpy(dtype=np.float32)
        for end in range(lookback - 1, len(group)):
            windows.append(values[end - lookback + 1 : end + 1])
            targets.append(bool(group.iloc[end]["_target"]))
            timestamps.append(group.iloc[end]["_timestamp"])
    if not windows:
        raise DeepLearningError("no symbol has enough rows for the configured temporal lookback")
    return TemporalSequenceDataset(
        sequences=np.stack(windows).astype(np.float32),
        targets=np.asarray(targets, dtype=np.float32),
        timestamps=pd.Series(pd.to_datetime(timestamps, utc=True)),
        feature_names=tuple(dataset.features.columns),
    )


def deep_learning_model_definitions() -> tuple[DeepLearningModelDefinition, ...]:
    """Return the four initial temporal neural architectures for Phase 20 research."""
    return (
        DeepLearningModelDefinition("lstm", _LstmClassifier),
        DeepLearningModelDefinition("gru", _GruClassifier),
        DeepLearningModelDefinition("temporal_cnn", _TemporalCnnClassifier),
        DeepLearningModelDefinition("transformer", _TransformerClassifier),
    )


class TorchTemporalClassifier:
    """Small deterministic CPU trainer that exposes sklearn-like binary probabilities."""

    def __init__(self, definition: DeepLearningModelDefinition, config: DeepLearningConfig) -> None:
        self._definition = definition
        self._config = config
        self._scaler: StandardScaler | None = None
        self._model: nn.Module | None = None

    def fit(self, sequences: np.ndarray, targets: np.ndarray, *, random_state: int) -> None:
        _validate_training_arrays(sequences, targets)
        torch.manual_seed(random_state)
        torch.use_deterministic_algorithms(True, warn_only=True)
        self._scaler = StandardScaler().fit(sequences.reshape(-1, sequences.shape[-1]))
        scaled = _transform_sequences(sequences, self._scaler)
        self._model = self._definition.factory(scaled.shape[-1], self._config)
        optimizer = torch.optim.Adam(self._model.parameters(), lr=self._config.learning_rate)
        loss_function = nn.BCEWithLogitsLoss()
        features = torch.from_numpy(scaled)
        labels = torch.from_numpy(targets.astype(np.float32)).unsqueeze(1)
        self._model.train()
        for _ in range(self._config.epochs):
            for start in range(0, len(features), self._config.batch_size):
                end = start + self._config.batch_size
                optimizer.zero_grad()
                loss = loss_function(self._model(features[start:end]), labels[start:end])
                loss.backward()
                optimizer.step()

    def predict_proba(self, sequences: np.ndarray) -> np.ndarray:
        if self._scaler is None or self._model is None:
            raise DeepLearningError("temporal classifier must be fitted before prediction")
        if sequences.ndim != 3:
            raise DeepLearningError("temporal prediction sequences must be three-dimensional")
        self._model.eval()
        with torch.no_grad():
            logits = self._model(torch.from_numpy(_transform_sequences(sequences, self._scaler)))
        return torch.sigmoid(logits).squeeze(1).numpy()


def _validate_training_arrays(sequences: np.ndarray, targets: np.ndarray) -> None:
    if sequences.ndim != 3 or not len(sequences):
        raise DeepLearningError(
            "temporal training sequences must be a non-empty three-dimensional array"
        )
    if len(sequences) != len(targets):
        raise DeepLearningError("temporal training sequences and targets must align")
    if len(np.unique(targets)) < 2:
        raise DeepLearningError("temporal training targets must contain both classes")


def _transform_sequences(sequences: np.ndarray, scaler: StandardScaler) -> np.ndarray:
    shape = sequences.shape
    return scaler.transform(sequences.reshape(-1, shape[-1])).reshape(shape).astype(np.float32)


class _LstmClassifier(nn.Module):
    def __init__(self, feature_count: int, config: DeepLearningConfig) -> None:
        super().__init__()
        self._lstm = nn.LSTM(feature_count, config.hidden_size, batch_first=True)
        self._head = nn.Linear(config.hidden_size, 1)

    def forward(self, values: Tensor) -> Tensor:
        output, _ = self._lstm(values)
        return self._head(output[:, -1])


class _GruClassifier(nn.Module):
    def __init__(self, feature_count: int, config: DeepLearningConfig) -> None:
        super().__init__()
        self._gru = nn.GRU(feature_count, config.hidden_size, batch_first=True)
        self._head = nn.Linear(config.hidden_size, 1)

    def forward(self, values: Tensor) -> Tensor:
        output, _ = self._gru(values)
        return self._head(output[:, -1])


class _TemporalCnnClassifier(nn.Module):
    def __init__(self, feature_count: int, config: DeepLearningConfig) -> None:
        super().__init__()
        self._convolution = nn.Conv1d(feature_count, config.hidden_size, kernel_size=3, padding=1)
        self._head = nn.Linear(config.hidden_size, 1)

    def forward(self, values: Tensor) -> Tensor:
        encoded = torch.relu(self._convolution(values.transpose(1, 2)))
        return self._head(encoded.mean(dim=2))


class _TransformerClassifier(nn.Module):
    def __init__(self, feature_count: int, config: DeepLearningConfig) -> None:
        super().__init__()
        self._embedding = nn.Linear(feature_count, config.hidden_size)
        self._position = nn.Parameter(torch.zeros(1, config.lookback, config.hidden_size))
        layer = nn.TransformerEncoderLayer(
            d_model=config.hidden_size,
            nhead=2,
            dim_feedforward=config.hidden_size * 2,
            dropout=0,
            batch_first=True,
        )
        self._encoder = nn.TransformerEncoder(layer, num_layers=1)
        self._head = nn.Linear(config.hidden_size, 1)

    def forward(self, values: Tensor) -> Tensor:
        encoded = self._embedding(values) + self._position[:, : values.shape[1]]
        return self._head(self._encoder(encoded)[:, -1])
