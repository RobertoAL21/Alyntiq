import argparse
import json

from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.features.constants import FEATURE_VERSION_V1
from app.features.service import FeatureBuildError, FeatureEngineeringService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build versioned, point-in-time features from stored historical market bars"
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
        help="Stored bar timeframe; only daily bars are available in Phase 3",
    )
    parser.add_argument(
        "--feature-version",
        default=FEATURE_VERSION_V1,
        help="Immutable feature set version to store",
    )
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    configure_logging()
    service = FeatureEngineeringService()

    try:
        with SessionLocal.begin() as session:
            result = service.build(
                session=session,
                source=arguments.source,
                timeframe=arguments.timeframe,
                feature_version=arguments.feature_version,
            )
    except FeatureBuildError as error:
        raise SystemExit(f"Feature build failed: {error}") from error

    print(
        json.dumps(
            {
                "feature_version": result.feature_version,
                "received": result.storage.received,
                "inserted": result.storage.inserted,
                "skipped": result.storage.skipped,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
