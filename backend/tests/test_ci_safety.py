import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath

import pytest


def _tracked_secret_failures(paths: tuple[PurePosixPath, ...]) -> list[str]:
    script_path = Path(__file__).resolve().parents[2] / "scripts/verify_ci_safety.py"
    specification = importlib.util.spec_from_file_location("verify_ci_safety", script_path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module._tracked_secret_failures(paths)


def test_ci_safety_contracts_pass_for_the_tracked_repository() -> None:
    if shutil.which("git") is None:
        pytest.skip("the production runtime image intentionally excludes git")
    repository_root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [sys.executable, str(repository_root / "scripts/verify_ci_safety.py")],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "CI safety checks passed"


def test_ci_safety_rejects_tracked_secret_files() -> None:
    failures = _tracked_secret_failures(
        (PurePosixPath(".env"), PurePosixPath("infrastructure/deploy.key"))
    )

    assert failures == [
        "tracked environment file is forbidden: .env",
        "tracked credential file is forbidden: infrastructure/deploy.key",
    ]


def test_ci_workflow_has_required_validation_and_no_release_step() -> None:
    workflow = (Path(__file__).resolve().parents[2] / ".github/workflows/ci.yml").read_text()

    for job in ("backend-quality:", "frontend-quality:", "financial-safety:", "docker-build:"):
        assert job in workflow
    assert "python ../scripts/verify_ci_safety.py" in workflow
    assert "docker build --tag alyntiq-backend:ci backend" in workflow
    assert "docker build --tag alyntiq-frontend:ci frontend" in workflow
    assert "docker push" not in workflow
