import json
import sys
from contextlib import nullcontext
from datetime import UTC, datetime

import pytest

from app.core.config import Settings
from app.paper_worker.types import PaperWorkerPreflight, PaperWorkerPreflightOutcome
from scripts import run_paper_worker


def test_worker_cli_requires_explicit_single_cycle_acknowledgement() -> None:
    with pytest.raises(SystemExit):
        run_paper_worker.build_parser().parse_args([])


def test_worker_cli_prints_persisted_preflight_summary(monkeypatch, capsys) -> None:
    session = _Session()
    monkeypatch.setattr(run_paper_worker, "SessionLocal", lambda: nullcontext(session))
    monkeypatch.setattr(run_paper_worker, "get_settings", lambda: Settings(_env_file=None))
    monkeypatch.setattr(run_paper_worker, "PaperWorkerService", _Worker)
    monkeypatch.setattr(sys, "argv", ["run_paper_worker", "--once"])

    assert run_paper_worker.main() == 0

    output = json.loads(capsys.readouterr().out)
    assert output["checked"] == 2
    assert output["ready"] == 1
    assert output["blocked"] == 1
    assert session.committed


class _Session:
    committed = False

    def commit(self) -> None:
        self.committed = True


class _Worker:
    def run_once(self, session, *, settings):
        return (
            PaperWorkerPreflight(
                deployment_id="deployment-ready",
                outcome=PaperWorkerPreflightOutcome.READY,
                reason="eligible",
                checked_at=datetime(2026, 9, 25, tzinfo=UTC),
            ),
            PaperWorkerPreflight(
                deployment_id="deployment-blocked",
                outcome=PaperWorkerPreflightOutcome.BLOCKED,
                reason="not production",
                checked_at=datetime(2026, 9, 25, tzinfo=UTC),
            ),
        )
