import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.advanced import AdvancedModelDefinition, advanced_model_definitions
from app.models.advanced_types import AdvancedModelRunResult, LeaderboardEntry
from app.models.dataset import TrainingDataset
from app.models.metrics import calculate_binary_metrics
from app.models.optimization import OptimizationError, optimize_model
from app.models.repository import TrainingDatasetError, load_training_dataset
from app.models.service_types import FoldResult
from app.models.tracking import MlflowTracker
from app.models.validation import (
    WalkForwardFold,
    WalkForwardValidationError,
    expanding_window_splits,
)

logger = logging.getLogger(__name__)

ADVANCED_MODEL_VERSION = "advanced-v1"


class AdvancedExperimentError(ValueError):
    """Raised when advanced models cannot be tuned and evaluated reproducibly."""


@dataclass(frozen=True)
class AdvancedExperimentResult:
    dataset: TrainingDataset
    runs: tuple[AdvancedModelRunResult, ...]
    leaderboard: tuple[LeaderboardEntry, ...]


class AdvancedExperimentService:
    """Tune advanced tree models on validation folds and evaluate once on a holdout fold."""

    def __init__(self, tracker: MlflowTracker) -> None:
        self._tracker = tracker

    def run(
        self,
        session: Session,
        *,
        source: str,
        timeframe: str,
        feature_version: str,
        target_version: str,
        dataset_version: str,
        n_splits: int,
        gap: int,
        n_trials: int,
        random_state: int,
        model_version: str = ADVANCED_MODEL_VERSION,
    ) -> AdvancedExperimentResult:
        if n_splits < 3:
            raise AdvancedExperimentError("n_splits must be at least 3 to reserve a holdout fold")
        try:
            dataset = load_training_dataset(
                session,
                source=source,
                timeframe=timeframe,
                feature_version=feature_version,
                target_version=target_version,
                dataset_version=dataset_version,
            )
            folds = expanding_window_splits(dataset.timestamps, n_splits=n_splits, gap=gap)
        except (TrainingDatasetError, WalkForwardValidationError) as error:
            raise AdvancedExperimentError(str(error)) from error

        validation_folds = folds[:-1]
        holdout_fold = folds[-1]
        try:
            runs = tuple(
                self._evaluate_definition(
                    dataset,
                    definition,
                    validation_folds,
                    holdout_fold,
                    n_trials=n_trials,
                    random_state=random_state,
                    model_version=model_version,
                )
                for definition in advanced_model_definitions()
            )
        except OptimizationError as error:
            raise AdvancedExperimentError(str(error)) from error

        leaderboard = build_leaderboard(runs)
        for run in runs:
            self._tracker.log_advanced(run, dataset.metadata)
            logger.info(
                "advanced_model_evaluated",
                extra={
                    "model_name": run.model_name,
                    "model_version": run.model_version,
                    "dataset_version": dataset.metadata.dataset_version,
                    "feature_version": dataset.metadata.feature_version,
                    "target_version": dataset.metadata.target_version,
                    "holdout_roc_auc": run.holdout.metrics.roc_auc,
                },
            )
        self._tracker.log_leaderboard(leaderboard, dataset.metadata, model_version)
        return AdvancedExperimentResult(dataset=dataset, runs=runs, leaderboard=leaderboard)

    def _evaluate_definition(
        self,
        dataset: TrainingDataset,
        definition: AdvancedModelDefinition,
        validation_folds: list[WalkForwardFold],
        holdout_fold: WalkForwardFold,
        *,
        n_trials: int,
        random_state: int,
        model_version: str,
    ) -> AdvancedModelRunResult:
        optimization = optimize_model(
            dataset,
            definition,
            validation_folds,
            n_trials=n_trials,
            random_state=random_state,
        )
        model = definition.factory(optimization.best_parameters, random_state)
        training_features = dataset.features.iloc[holdout_fold.train_indices]
        training_target = dataset.target.iloc[holdout_fold.train_indices]
        test_features = dataset.features.iloc[holdout_fold.test_indices]
        test_target = dataset.target.iloc[holdout_fold.test_indices]
        model.fit(training_features, training_target)
        probabilities = model.predict_proba(test_features)[:, 1]
        importance = {
            feature: float(value)
            for feature, value in zip(
                dataset.features.columns, model.feature_importances_, strict=True
            )
        }
        return AdvancedModelRunResult(
            model_name=definition.name,
            model_version=model_version,
            row_count=dataset.row_count,
            optimization=optimization,
            holdout=FoldResult(
                number=holdout_fold.number,
                train_rows=len(training_features),
                test_rows=len(test_features),
                metrics=calculate_binary_metrics(test_target, probabilities),
            ),
            feature_importance=dict(
                sorted(importance.items(), key=lambda item: item[1], reverse=True)
            ),
        )


def build_leaderboard(
    runs: tuple[AdvancedModelRunResult, ...],
) -> tuple[LeaderboardEntry, ...]:
    """Rank advanced models by their untouched holdout ROC-AUC, then holdout accuracy."""
    ordered_runs = sorted(
        runs,
        key=lambda run: (
            run.holdout.metrics.roc_auc is not None,
            run.holdout.metrics.roc_auc or float("-inf"),
            run.holdout.metrics.accuracy,
        ),
        reverse=True,
    )
    return tuple(
        LeaderboardEntry(
            rank=index,
            model_name=run.model_name,
            holdout_roc_auc=run.holdout.metrics.roc_auc,
            holdout_accuracy=run.holdout.metrics.accuracy,
        )
        for index, run in enumerate(ordered_runs, start=1)
    )
