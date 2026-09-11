import logging
from dataclasses import dataclass

import pandas as pd
from sqlalchemy.orm import Session

from app.models.baselines import baseline_definitions
from app.models.dataset import TrainingDataset
from app.models.metrics import calculate_binary_metrics
from app.models.repository import TrainingDatasetError, load_training_dataset
from app.models.service_types import BaselineRunResult, FoldResult
from app.models.tracking import MlflowTracker
from app.models.validation import WalkForwardValidationError, expanding_window_splits

logger = logging.getLogger(__name__)

BASELINE_MODEL_VERSION = "baselines-v1"


class BaselineExperimentError(ValueError):
    """Raised when baseline models cannot be evaluated reproducibly."""


@dataclass(frozen=True)
class BaselineExperimentResult:
    dataset: TrainingDataset
    runs: tuple[BaselineRunResult, ...]


class BaselineExperimentService:
    """Evaluate Phase 5 baselines with expanding chronological validation windows."""

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
        random_state: int,
        model_version: str = BASELINE_MODEL_VERSION,
    ) -> BaselineExperimentResult:
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
            raise BaselineExperimentError(str(error)) from error

        runs = tuple(
            self._run_definition(dataset, definition, folds, random_state, model_version)
            for definition in baseline_definitions()
        )
        for run in runs:
            self._tracker.log(run, dataset.metadata)
            logger.info(
                "baseline_model_evaluated",
                extra={
                    "model_name": run.model_name,
                    "model_version": run.model_version,
                    "dataset_version": dataset.metadata.dataset_version,
                    "feature_version": dataset.metadata.feature_version,
                    "target_version": dataset.metadata.target_version,
                    "row_count": run.row_count,
                },
            )
        return BaselineExperimentResult(dataset=dataset, runs=runs)

    def _run_definition(self, dataset, definition, folds, random_state, model_version):
        fold_results = []
        for fold in folds:
            model = definition.factory(random_state + fold.number)
            training_features = dataset.features.iloc[fold.train_indices]
            training_target = dataset.target.iloc[fold.train_indices]
            test_features = dataset.features.iloc[fold.test_indices]
            test_target = dataset.target.iloc[fold.test_indices]
            model.fit(training_features, training_target)
            probabilities = model.predict_proba(test_features)[:, 1]
            fold_results.append(
                FoldResult(
                    number=fold.number,
                    train_rows=len(training_features),
                    test_rows=len(test_features),
                    metrics=calculate_binary_metrics(test_target, probabilities),
                )
            )

        averages = _average_metrics(fold_results)
        return BaselineRunResult(
            model_name=definition.name,
            model_version=model_version,
            parameters=definition.parameters,
            row_count=dataset.row_count,
            folds=tuple(fold_results),
            average_metrics=averages,
        )


def _average_metrics(folds: list[FoldResult]) -> dict[str, float | None]:
    metrics = pd.DataFrame([fold.metrics.as_dict() for fold in folds])
    return {
        name: None if metrics[name].dropna().empty else float(metrics[name].mean())
        for name in metrics.columns
    }
