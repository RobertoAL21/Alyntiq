#!/usr/bin/env python3
"""Fail CI when tracked files violate Alyntiq's paper-trading safety contracts."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path, PurePosixPath

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SENSITIVE_ENVIRONMENT_VARIABLES = frozenset(
    {
        "ALPACA_API_KEY",
        "ALPACA_SECRET_KEY",
        "POSTGRES_PASSWORD",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
    }
)
SAFE_PLACEHOLDERS = frozenset({"", "replace-me"})


def main() -> int:
    tracked_files = _tracked_files()
    failures = [
        *_tracked_secret_failures(tracked_files),
        *_example_environment_failures(tracked_files),
        *_paper_trading_failures(),
        *_model_lineage_failures(),
    ]
    if failures:
        print("CI safety checks failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("CI safety checks passed")
    return 0


def _tracked_files() -> tuple[PurePosixPath, ...]:
    output = subprocess.check_output(["git", "ls-files", "-z"], cwd=REPOSITORY_ROOT, text=False)
    return tuple(PurePosixPath(path.decode()) for path in output.split(b"\0") if path)


def _tracked_secret_failures(tracked_files: tuple[PurePosixPath, ...]) -> list[str]:
    failures = []
    forbidden_suffixes = (".pem", ".key", ".crt", ".p12")
    for path in tracked_files:
        name = path.name
        if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
            failures.append(f"tracked environment file is forbidden: {path}")
        if name.endswith(forbidden_suffixes):
            failures.append(f"tracked credential file is forbidden: {path}")
    return failures


def _example_environment_failures(tracked_files: tuple[PurePosixPath, ...]) -> list[str]:
    example_path = PurePosixPath(".env.example")
    if example_path not in tracked_files:
        return [".env.example must remain tracked"]
    failures = []
    for line in (REPOSITORY_ROOT / example_path).read_text().splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", maxsplit=1)
        if name in SENSITIVE_ENVIRONMENT_VARIABLES and value not in SAFE_PLACEHOLDERS:
            failures.append(f"{name} in .env.example must be blank or a safe placeholder")
    return failures


def _paper_trading_failures() -> list[str]:
    settings = (REPOSITORY_ROOT / "backend/app/core/config.py").read_text()
    broker = (REPOSITORY_ROOT / "backend/app/execution/alpaca.py").read_text()
    environment_example = (REPOSITORY_ROOT / ".env.example").read_text()
    failures = []
    if 'trading_environment: Literal["paper", "live"] = "paper"' not in settings:
        failures.append("Settings must default TRADING_ENVIRONMENT to paper")
    if "TRADING_ENVIRONMENT=paper" not in environment_example:
        failures.append(".env.example must set TRADING_ENVIRONMENT=paper")
    if 'trading_environment != "paper"' not in broker:
        failures.append("paper broker must reject non-paper environments")
    if "https://paper-api.alpaca.markets/v2" not in broker:
        failures.append("paper broker must use Alpaca's paper endpoint")
    if "https://api.alpaca.markets" in broker:
        failures.append("live Alpaca endpoint is forbidden in the paper broker")
    return failures


def _model_lineage_failures() -> list[str]:
    strategy = (REPOSITORY_ROOT / "backend/app/strategies/ml.py").read_text()
    if "if not self.model_version.strip():" not in strategy:
        return ["ML predictions must require a non-blank model_version"]
    return []


if __name__ == "__main__":
    raise SystemExit(main())
