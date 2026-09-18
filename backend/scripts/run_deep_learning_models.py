import argparse
import json

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.models.deep_learning import DeepLearningConfig
from app.models.deep_learning_service import (
    DEEP_LEARNING_MODEL_VERSION,
    DeepLearningExperimentError,
    DeepLearningExperimentService,
)
from app.models.repository import TrainingDatasetError, load_training_dataset
from app.models.tracking import MlflowTracker
from app.observability.telemetry import configure_observability


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate temporal neural classifiers on chronological validation and holdout folds"
        )
    )
    parser.add_argument("--source", default="alpaca:iex:raw")
    parser.add_argument("--timeframe", default="1D", choices=["1D"])
    parser.add_argument("--feature-version", default="features-v1")
    parser.add_argument("--target-version", default="targets-v1")
    parser.add_argument("--dataset-version", default="dataset-v1")
    parser.add_argument("--model-version", default=DEEP_LEARNING_MODEL_VERSION)
    parser.add_argument("--n-splits", default=3, type=int)
    parser.add_argument("--gap", default=1, type=int)
    parser.add_argument("--lookback", default=20, type=int)
    parser.add_argument("--hidden-size", default=16, type=int)
    parser.add_argument("--epochs", default=10, type=int)
    parser.add_argument("--batch-size", default=32, type=int)
    parser.add_argument("--learning-rate", default=0.001, type=float)
    parser.add_argument("--random-state", default=42, type=int)
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    configure_logging()
    settings = get_settings()
    configure_observability(settings)
    try:
        config = DeepLearningConfig(
            lookback=arguments.lookback,
            hidden_size=arguments.hidden_size,
            epochs=arguments.epochs,
            batch_size=arguments.batch_size,
            learning_rate=arguments.learning_rate,
            random_state=arguments.random_state,
        )
        with SessionLocal() as session:
            dataset = load_training_dataset(
                session,
                source=arguments.source,
                timeframe=arguments.timeframe,
                feature_version=arguments.feature_version,
                target_version=arguments.target_version,
                dataset_version=arguments.dataset_version,
            )
        result = DeepLearningExperimentService(
            MlflowTracker(
                settings.mlflow_tracking_uri,
                settings.mlflow_artifact_uri,
                settings.mlflow_experiment_name,
            )
        ).run(
            dataset,
            config=config,
            n_splits=arguments.n_splits,
            gap=arguments.gap,
            model_version=arguments.model_version,
        )
    except (DeepLearningExperimentError, TrainingDatasetError, ValueError) as error:
        raise SystemExit(f"Deep-learning evaluation failed: {error}") from error

    print(
        json.dumps(
            {
                "dataset_version": dataset.metadata.dataset_version,
                "sequences": len(result.sequences.sequences),
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
