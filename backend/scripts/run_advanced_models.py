import argparse
import json

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.models.advanced_service import AdvancedExperimentError, AdvancedExperimentService
from app.models.tracking import MlflowTracker
from app.observability.telemetry import configure_observability


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tune advanced tree classifiers and evaluate them on a reserved holdout fold"
    )
    parser.add_argument("--source", default="alpaca:iex:raw")
    parser.add_argument("--timeframe", default="1D", choices=["1D"])
    parser.add_argument("--feature-version", default="features-v1")
    parser.add_argument("--target-version", default="targets-v1")
    parser.add_argument("--dataset-version", default="dataset-v1")
    parser.add_argument("--model-version", default="advanced-v1")
    parser.add_argument("--n-splits", default=3, type=int)
    parser.add_argument("--gap", default=1, type=int)
    parser.add_argument("--n-trials", default=10, type=int)
    parser.add_argument("--random-state", default=42, type=int)
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    configure_logging()
    settings = get_settings()
    configure_observability(settings)
    service = AdvancedExperimentService(
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
                n_trials=arguments.n_trials,
                random_state=arguments.random_state,
            )
    except AdvancedExperimentError as error:
        raise SystemExit(f"Advanced-model evaluation failed: {error}") from error

    print(
        json.dumps(
            {
                "dataset_version": result.dataset.metadata.dataset_version,
                "rows": result.dataset.row_count,
                "leaderboard": [
                    {
                        "rank": entry.rank,
                        "model_name": entry.model_name,
                        "holdout_roc_auc": entry.holdout_roc_auc,
                        "holdout_accuracy": entry.holdout_accuracy,
                    }
                    for entry in result.leaderboard
                ],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
