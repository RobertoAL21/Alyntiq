import logging
from dataclasses import dataclass
from time import perf_counter

import numpy as np
import pandas as pd

from app.models.baselines import BaselineDefinition, baseline_definitions
from app.models.dataset import TrainingDataset
from app.models.deep_learning import (
    DeepLearningConfig,
    DeepLearningError,
    DeepLearningModelDefinition,
    TemporalSequenceDataset,
    TorchTemporalClassifier,
    build_temporal_sequences,
    deep_learning_model_definitions,
)
from app.models.metrics import BinaryClassificationMetrics, calculate_binary_metrics
from app.models.service_types import FoldResult
from app.models.tracking import MlflowTracker
from app.models.validation import (
    WalkForwardFold,
    WalkForwardValidationError,
    expanding_window_splits,
)
from app.observability.telemetry import get_telemetry

DEEP_LEARNING_MODEL_VERSION = "temporal-v1"

logger = logging.getLogger(__name__)


class DeepLearningExperimentError(ValueError):
    """Raised when temporal models cannot be evaluated under chronological assumptions."""


@dataclass(frozen=True)
class DeepLearningRunResult:
    model_name: str
    model_family: str
    model_version: str
    sequence_count: int
    validation_folds: tuple[FoldResult, ...]
    mean_validation_metrics: BinaryClassificationMetrics
    holdout: FoldResult


@dataclass(frozen=True)
class DeepLearningLeaderboardEntry:
    rank: int
    model_name: str
    holdout_roc_auc: float | None
    holdout_accuracy: float


@dataclass(frozen=True)
class DeepLearningExperimentResult:
    sequences: TemporalSequenceDataset
    runs: tuple[DeepLearningRunResult, ...]
    leaderboard: tuple[DeepLearningLeaderboardEntry, ...]


class DeepLearningExperimentService:
    """Evaluate fixed temporal neural models with validation folds and one reserved holdout."""

    def __init__(self, tracker: MlflowTracker | None = None) -> None:
        self._tracker = tracker

    def run(
        self,
        dataset: TrainingDataset,
        *,
        config: DeepLearningConfig,
        n_splits: int,
        gap: int,
        model_version: str = DEEP_LEARNING_MODEL_VERSION,
    ) -> DeepLearningExperimentResult:
        if n_splits < 3:
            raise DeepLearningExperimentError(
                "n_splits must be at least 3 to reserve a holdout fold"
            )
        try:
            sequences = build_temporal_sequences(dataset, lookback=config.lookback)
            folds = expanding_window_splits(sequences.timestamps, n_splits=n_splits, gap=gap)
        except (DeepLearningError, WalkForwardValidationError) as error:
            raise DeepLearningExperimentError(str(error)) from error

        validation_folds = folds[:-1]
        holdout_fold = folds[-1]
        try:
            deep_learning_runs = tuple(
                _evaluate_definition(
                    definition,
                    sequences,
                    validation_folds,
                    holdout_fold,
                    config=config,
                    model_version=model_version,
                    definition_number=number,
                )
                for number, definition in enumerate(deep_learning_model_definitions())
            )
            baseline_runs = tuple(
                _evaluate_baseline_definition(
                    definition,
                    sequences,
                    validation_folds,
                    holdout_fold,
                    random_state=config.random_state + (number * 1_000),
                    model_version=model_version,
                )
                for number, definition in enumerate(baseline_definitions())
            )
        except DeepLearningError as error:
            raise DeepLearningExperimentError(str(error)) from error
        runs = deep_learning_runs + baseline_runs
        leaderboard = build_deep_learning_leaderboard(runs)
        if self._tracker is not None:
            for run in runs:
                self._tracker.log_deep_learning(run, dataset.metadata, config)
                logger.info(
                    "deep_learning_model_evaluated",
                    extra={
                        "model_name": run.model_name,
                        "model_version": run.model_version,
                        "dataset_version": dataset.metadata.dataset_version,
                        "feature_version": dataset.metadata.feature_version,
                        "target_version": dataset.metadata.target_version,
                        "holdout_roc_auc": run.holdout.metrics.roc_auc,
                    },
                )
            self._tracker.log_deep_learning_leaderboard(
                leaderboard, dataset.metadata, model_version
            )
        return DeepLearningExperimentResult(
            sequences=sequences,
            runs=runs,
            leaderboard=leaderboard,
        )


def _evaluate_definition(
    definition: DeepLearningModelDefinition,
    sequences: TemporalSequenceDataset,
    validation_folds: list[WalkForwardFold],
    holdout_fold: WalkForwardFold,
    *,
    config: DeepLearningConfig,
    model_version: str,
    definition_number: int,
) -> DeepLearningRunResult:
    validation = tuple(
        _evaluate_fold(
            definition,
            sequences,
            fold,
            config=config,
            model_version=model_version,
            random_state=config.random_state + (definition_number * 1_000) + fold.number,
        )
        for fold in validation_folds
    )
    holdout = _evaluate_fold(
        definition,
        sequences,
        holdout_fold,
        config=config,
        model_version=model_version,
        random_state=config.random_state + (definition_number * 1_000) + holdout_fold.number,
    )
    return DeepLearningRunResult(
        model_name=definition.name,
        model_family="deep_learning",
        model_version=model_version,
        sequence_count=len(sequences.sequences),
        validation_folds=validation,
        mean_validation_metrics=_mean_metrics(tuple(fold.metrics for fold in validation)),
        holdout=holdout,
    )


def _evaluate_baseline_definition(
    definition: BaselineDefinition,
    sequences: TemporalSequenceDataset,
    validation_folds: list[WalkForwardFold],
    holdout_fold: WalkForwardFold,
    *,
    random_state: int,
    model_version: str,
) -> DeepLearningRunResult:
    validation = tuple(
        _evaluate_baseline_fold(
            definition,
            sequences,
            fold,
            model_version=model_version,
            random_state=random_state + fold.number,
        )
        for fold in validation_folds
    )
    holdout = _evaluate_baseline_fold(
        definition,
        sequences,
        holdout_fold,
        model_version=model_version,
        random_state=random_state + holdout_fold.number,
    )
    return DeepLearningRunResult(
        model_name=f"baseline_{definition.name}",
        model_family="baseline",
        model_version=model_version,
        sequence_count=len(sequences.sequences),
        validation_folds=validation,
        mean_validation_metrics=_mean_metrics(tuple(fold.metrics for fold in validation)),
        holdout=holdout,
    )


def _evaluate_fold(
    definition: DeepLearningModelDefinition,
    sequences: TemporalSequenceDataset,
    fold: WalkForwardFold,
    *,
    config: DeepLearningConfig,
    model_version: str,
    random_state: int,
) -> FoldResult:
    classifier = TorchTemporalClassifier(definition, config)
    train_sequences = sequences.sequences[fold.train_indices]
    train_targets = sequences.targets[fold.train_indices]
    test_sequences = sequences.sequences[fold.test_indices]
    test_targets = sequences.targets[fold.test_indices]
    classifier.fit(train_sequences, train_targets, random_state=random_state)
    prediction_started_at = perf_counter()
    probabilities = classifier.predict_proba(test_sequences)
    get_telemetry().record_prediction(
        model_name=definition.name,
        model_version=model_version,
        count=len(probabilities),
        duration_seconds=perf_counter() - prediction_started_at,
    )
    return FoldResult(
        number=fold.number,
        train_rows=len(train_sequences),
        test_rows=len(test_sequences),
        metrics=calculate_binary_metrics(pd.Series(test_targets.astype(bool)), probabilities),
    )


def _evaluate_baseline_fold(
    definition: BaselineDefinition,
    sequences: TemporalSequenceDataset,
    fold: WalkForwardFold,
    *,
    model_version: str,
    random_state: int,
) -> FoldResult:
    """Evaluate an existing simple model on each window's latest feature observation."""
    features = sequences.sequences[:, -1, :]
    model = definition.factory(random_state)
    training_features = features[fold.train_indices]
    training_target = pd.Series(sequences.targets[fold.train_indices].astype(bool))
    test_features = features[fold.test_indices]
    test_target = pd.Series(sequences.targets[fold.test_indices].astype(bool))
    model.fit(training_features, training_target)
    prediction_started_at = perf_counter()
    probabilities = model.predict_proba(test_features)[:, 1]
    get_telemetry().record_prediction(
        model_name=f"baseline_{definition.name}",
        model_version=model_version,
        count=len(probabilities),
        duration_seconds=perf_counter() - prediction_started_at,
    )
    return FoldResult(
        number=fold.number,
        train_rows=len(training_features),
        test_rows=len(test_features),
        metrics=calculate_binary_metrics(test_target, probabilities),
    )


def _mean_metrics(metrics: tuple[BinaryClassificationMetrics, ...]) -> BinaryClassificationMetrics:
    if not metrics:
        raise DeepLearningExperimentError("at least one validation fold is required")
    return BinaryClassificationMetrics(
        accuracy=float(np.mean([item.accuracy for item in metrics])),
        precision=float(np.mean([item.precision for item in metrics])),
        recall=float(np.mean([item.recall for item in metrics])),
        f1=float(np.mean([item.f1 for item in metrics])),
        roc_auc=(
            None
            if not [item.roc_auc for item in metrics if item.roc_auc is not None]
            else float(np.mean([item.roc_auc for item in metrics if item.roc_auc is not None]))
        ),
    )


def build_deep_learning_leaderboard(
    runs: tuple[DeepLearningRunResult, ...],
) -> tuple[DeepLearningLeaderboardEntry, ...]:
    """Rank only untouched predictive holdout metrics; this is not trading performance."""
    ordered = sorted(
        runs,
        key=lambda run: (
            run.holdout.metrics.roc_auc is not None,
            run.holdout.metrics.roc_auc or float("-inf"),
            run.holdout.metrics.accuracy,
        ),
        reverse=True,
    )
    return tuple(
        DeepLearningLeaderboardEntry(
            rank=index,
            model_name=run.model_name,
            holdout_roc_auc=run.holdout.metrics.roc_auc,
            holdout_accuracy=run.holdout.metrics.accuracy,
        )
        for index, run in enumerate(ordered, start=1)
    )
