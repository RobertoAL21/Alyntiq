import argparse
import json

from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.model_registry.service import ModelLifecycleError, ModelRegistryService
from app.model_registry.types import ModelRegistration, RegisteredModel


def _json_object(value: str) -> dict[str, object]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        raise argparse.ArgumentTypeError("must be valid JSON") from error
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("must be a JSON object")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Register a reproducible model version as a candidate"
    )
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--model-version", required=True)
    parser.add_argument("--model-family", required=True)
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--feature-version", required=True)
    parser.add_argument("--target-version", required=True)
    parser.add_argument("--parameters", default="{}", type=_json_object)
    parser.add_argument("--metrics", required=True, type=_json_object)
    parser.add_argument("--backtest-results", required=True, type=_json_object)
    parser.add_argument("--artifact-uri", required=True)
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    configure_logging()
    try:
        registration = ModelRegistration(
            model_name=arguments.model_name,
            model_version=arguments.model_version,
            model_family=arguments.model_family,
            dataset_version=arguments.dataset_version,
            feature_version=arguments.feature_version,
            target_version=arguments.target_version,
            parameters=arguments.parameters,
            metrics=arguments.metrics,
            backtest_results=arguments.backtest_results,
            artifact_uri=arguments.artifact_uri,
        )
        with SessionLocal() as session:
            model = ModelRegistryService().register(session, registration)
            session.commit()
    except (ModelLifecycleError, ValueError) as error:
        raise SystemExit(f"Model registration failed: {error}") from error

    print(json.dumps(_as_output(model)))
    return 0


def _as_output(model: RegisteredModel) -> dict[str, object]:
    return {
        "id": model.id,
        "model_name": model.registration.model_name,
        "model_version": model.registration.model_version,
        "state": model.state.value,
        "artifact_uri": model.registration.artifact_uri,
    }


if __name__ == "__main__":
    raise SystemExit(main())
