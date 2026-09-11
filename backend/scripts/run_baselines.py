import argparse
import json

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.models.service import BaselineExperimentError, BaselineExperimentService
from app.models.tracking import MlflowTracker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate baseline classifiers with expanding walk-forward validation"
    )
    parser.add_argument("--source", default="alpaca:iex:raw")
    parser.add_argument("--timeframe", default="1D", choices=["1D"])
    parser.add_argument("--feature-version", default="features-v1")
    parser.add_argument("--target-version", default="targets-v1")
    parser.add_argument("--dataset-version", default="dataset-v1")
    parser.add_argument("--model-version", default="baselines-v1")
    parser.add_argument("--n-splits", default=3, type=int)
    parser.add_argument("--gap", default=1, type=int)
    parser.add_argument("--random-state", default=42, type=int)
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    configure_logging()
    settings = get_settings()
    service = BaselineExperimentService(
        MlflowTracker(
            settings.mlflow_tracking_uri,
            settings.mlflow_artifact_uri,
            settings.mlflow_experiment_name,
        )
    )
    try:
        with SessionLocal() as session:
            result = service.run(
                session,
                source=arguments.source,
                timeframe=arguments.timeframe,
                feature_version=arguments.feature_version,
                target_version=arguments.target_version,
                dataset_version=arguments.dataset_version,
                model_version=arguments.model_version,
                n_splits=arguments.n_splits,
                gap=arguments.gap,
                random_state=arguments.random_state,
            )
    except BaselineExperimentError as error:
        raise SystemExit(f"Baseline evaluation failed: {error}") from error

    print(
        json.dumps(
            {
                "dataset_version": result.dataset.metadata.dataset_version,
                "feature_version": result.dataset.metadata.feature_version,
                "target_version": result.dataset.metadata.target_version,
                "rows": result.dataset.row_count,
                "models": {run.model_name: run.average_metrics for run in result.runs},
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
