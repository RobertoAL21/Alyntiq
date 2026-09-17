import pytest

from scripts.run_deep_learning_models import build_parser


def test_deep_learning_cli_exposes_reproducible_temporal_settings() -> None:
    arguments = build_parser().parse_args(["--lookback", "30", "--epochs", "5"])

    assert arguments.lookback == 30
    assert arguments.epochs == 5
    assert arguments.model_version == "temporal-v1"


def test_deep_learning_cli_rejects_non_integer_temporal_settings() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--lookback", "not-a-number"])
