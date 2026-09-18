import pytest

from scripts.register_model import build_parser as build_register_parser
from scripts.set_model_state import build_parser as build_state_parser


def test_register_model_cli_requires_full_reproducibility_provenance() -> None:
    arguments = build_register_parser().parse_args(
        [
            "--model-name",
            "transformer",
            "--model-version",
            "transformer-v1",
            "--model-family",
            "deep_learning",
            "--dataset-version",
            "dataset-v1",
            "--feature-version",
            "features-v1",
            "--target-version",
            "targets-v1",
            "--metrics",
            '{"holdout_roc_auc": 0.61}',
            "--backtest-results",
            '{"sharpe_ratio": 0.8}',
            "--artifact-uri",
            "file:///artifacts/transformer-v1",
        ]
    )

    assert arguments.parameters == {}
    assert arguments.metrics == {"holdout_roc_auc": 0.61}
    assert arguments.backtest_results == {"sharpe_ratio": 0.8}


def test_model_state_cli_accepts_only_defined_lifecycle_states() -> None:
    arguments = build_state_parser().parse_args(
        ["--model-version", "transformer-v1", "--state", "production"]
    )

    assert arguments.state == "production"
    with pytest.raises(SystemExit):
        build_state_parser().parse_args(["--model-version", "transformer-v1", "--state", "live"])
