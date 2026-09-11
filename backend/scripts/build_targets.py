import argparse
import json

from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.targets.constants import TARGET_VERSION_V1
from app.targets.service import TargetBuildError, TargetGenerationService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build versioned supervised-learning targets from historical market bars"
    )
    parser.add_argument(
        "--source",
        default="alpaca:iex:raw",
        help="Stored market-data provenance to transform",
    )
    parser.add_argument(
        "--timeframe",
        default="1D",
        choices=["1D"],
        help="Stored bar timeframe; only daily bars are available in Phase 4",
    )
    parser.add_argument(
        "--target-version",
        default=TARGET_VERSION_V1,
        help="Immutable target set version to store",
    )
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    configure_logging()

    try:
        with SessionLocal.begin() as session:
            result = TargetGenerationService().build(
                session=session,
                source=arguments.source,
                timeframe=arguments.timeframe,
                target_version=arguments.target_version,
            )
    except TargetBuildError as error:
        raise SystemExit(f"Target build failed: {error}") from error

    print(
        json.dumps(
            {
                "target_version": result.target_version,
                "received": result.storage.received,
                "inserted": result.storage.inserted,
                "skipped": result.storage.skipped,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
