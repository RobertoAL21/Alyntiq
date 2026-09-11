import json
from dataclasses import asdict

import mlflow
from mlflow import MlflowClient

from app.models.dataset import DatasetMetadata
from app.models.service_types import BaselineRunResult


class MlflowTracker:
    """Record reproducible baseline experiments through MLflow's tracking interface."""

    def __init__(self, tracking_uri: str, artifact_uri: str, experiment_name: str) -> None:
        self._tracking_uri = tracking_uri
        self._artifact_uri = artifact_uri
        self._experiment_name = experiment_name

    def log(self, result: BaselineRunResult, metadata: DatasetMetadata) -> None:
        mlflow.set_tracking_uri(self._tracking_uri)
        client = MlflowClient()
        if client.get_experiment_by_name(self._experiment_name) is None:
            client.create_experiment(self._experiment_name, artifact_location=self._artifact_uri)
        mlflow.set_experiment(self._experiment_name)
        with mlflow.start_run(run_name=result.model_name):
            mlflow.log_params(
                {
                    "model_name": result.model_name,
                    "model_version": result.model_version,
                    "dataset_version": metadata.dataset_version,
                    "feature_version": metadata.feature_version,
                    "target_version": metadata.target_version,
                    "source": metadata.source,
                    "timeframe": metadata.timeframe,
                    "row_count": result.row_count,
                    "n_splits": len(result.folds),
                    **result.parameters,
                }
            )
            for fold in result.folds:
                mlflow.log_metrics(
                    {
                        key: value
                        for key, value in fold.metrics.as_dict().items()
                        if value is not None
                    },
                    step=fold.number,
                )
            mlflow.log_metrics(
                {key: value for key, value in result.average_metrics.items() if value is not None}
            )
            mlflow.log_text(
                json.dumps(asdict(result), default=str, indent=2), "baseline_result.json"
            )
