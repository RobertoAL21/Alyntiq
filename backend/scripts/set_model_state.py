import argparse
import json

from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.model_registry.service import ModelLifecycleError, ModelRegistryService
from app.model_registry.types import ModelState, RegisteredModel


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Promote, demote, or retire one registered model version"
    )
    parser.add_argument("--model-version", required=True)
    parser.add_argument("--state", required=True, choices=[state.value for state in ModelState])
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    configure_logging()
    try:
        with SessionLocal() as session:
            model = ModelRegistryService().transition(
                session,
                model_version=arguments.model_version,
                target_state=ModelState(arguments.state),
            )
            session.commit()
    except ModelLifecycleError as error:
        raise SystemExit(f"Model state update failed: {error}") from error

    print(json.dumps(_as_output(model)))
    return 0


def _as_output(model: RegisteredModel) -> dict[str, str]:
    return {
        "model_version": model.registration.model_version,
        "state": model.state.value,
        "updated_at": model.updated_at.isoformat(),
    }


if __name__ == "__main__":
    raise SystemExit(main())
