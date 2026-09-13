import pytest

from scripts.run_advanced_models import build_parser


def test_cli_defaults_to_a_reserved_holdout_and_optuna_trials() -> None:
    arguments = build_parser().parse_args([])

    assert arguments.model_version == "advanced-v1"
    assert arguments.n_splits == 3
    assert arguments.gap == 1
    assert arguments.n_trials == 10


def test_cli_rejects_non_daily_timeframes() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--timeframe", "1H"])
