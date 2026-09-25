import argparse
import json

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.paper_worker.service import PaperWorkerService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one non-executing paper-worker preflight for armed deployments"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        required=True,
        help="Required safety acknowledgement: run exactly one preflight cycle",
    )
    return parser


def main() -> int:
    build_parser().parse_args()
    configure_logging()
    with SessionLocal() as session:
        results = PaperWorkerService().run_once(session, settings=get_settings())
        session.commit()
    print(
        json.dumps(
            {
                "checked": len(results),
                "ready": sum(result.outcome.value == "ready" for result in results),
                "blocked": sum(result.outcome.value == "blocked" for result in results),
                "results": [
                    {
                        "deployment_id": result.deployment_id,
                        "outcome": result.outcome.value,
                        "reason": result.reason,
                        "checked_at": result.checked_at.isoformat(),
                    }
                    for result in results
                ],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
