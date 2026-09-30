import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.model_artifacts.linear import (
    LinearArtifactError,
    train_linear_artifact,
    write_linear_artifact,
)
from app.models.repository import TrainingDatasetError, load_training_dataset


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train a JSON-only logistic-regression artifact")
    parser.add_argument("--model-version", required=True)
    parser.add_argument("--source", default="alpaca:iex:raw")
    parser.add_argument("--timeframe", default="1D", choices=["1D"])
    parser.add_argument("--feature-version", default="features-v1")
    parser.add_argument("--target-version", default="targets-v1")
    parser.add_argument("--dataset-version", default="dataset-v1")
    parser.add_argument("--training-end", required=True, help="Inclusive UTC date, YYYY-MM-DD")
    parser.add_argument("--artifact-path", required=True, type=Path)
    parser.add_argument("--random-state", default=42, type=int)
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    configure_logging()
    try:
        cutoff = datetime.strptime(arguments.training_end, "%Y-%m-%d").replace(
            tzinfo=UTC
        ) + timedelta(days=1)
        with SessionLocal() as session:
            dataset = load_training_dataset(
                session,
                source=arguments.source,
                timeframe=arguments.timeframe,
                feature_version=arguments.feature_version,
                target_version=arguments.target_version,
                dataset_version=arguments.dataset_version,
            )
        artifact = train_linear_artifact(
            dataset,
            model_version=arguments.model_version,
            trained_through=cutoff,
            random_state=arguments.random_state,
        )
        uri = arguments.artifact_path.resolve().as_uri()
        write_linear_artifact(artifact, uri)
    except (LinearArtifactError, TrainingDatasetError, ValueError) as error:
        raise SystemExit(f"Linear artifact training failed: {error}") from error
    print(
        json.dumps(
            {
                "artifact_uri": uri,
                "training_rows": artifact.training_rows,
                "trained_through": artifact.trained_through.isoformat(),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
