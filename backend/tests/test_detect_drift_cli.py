import json
import sys

import pandas as pd
import pytest

from scripts.detect_drift import build_parser, main


def test_detect_drift_cli_requires_explicit_feature_contract() -> None:
    arguments = build_parser().parse_args(
        [
            "--reference-features",
            "training.csv",
            "--current-features",
            "live.csv",
            "--feature-columns",
            "returns_1d,momentum_5",
            "--feature-psi-threshold",
            "0.25",
        ]
    )

    assert arguments.feature_columns == "returns_1d,momentum_5"
    assert arguments.feature_psi_threshold == 0.25
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--reference-features", "training.csv"])


def test_detect_drift_cli_emits_structured_alerts(
    tmp_path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    reference_path = tmp_path / "reference.csv"
    current_path = tmp_path / "current.csv"
    pd.DataFrame({"momentum": [0.0] * 10}).to_csv(reference_path, index=False)
    pd.DataFrame({"momentum": [1.0] * 10}).to_csv(current_path, index=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "detect_drift",
            "--reference-features",
            str(reference_path),
            "--current-features",
            str(current_path),
            "--feature-columns",
            "momentum",
            "--feature-psi-threshold",
            "0.1",
        ],
    )

    assert main() == 0

    output = json.loads(capsys.readouterr().out)
    assert output["feature_distributions"][0]["drifted"]
    assert len(output["alerts"]) == 1
    assert output["alerts"][0]["kind"] == "feature"
    assert output["alerts"][0]["subject"] == "momentum"
    assert output["alerts"][0]["threshold"] == 0.1
