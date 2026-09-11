import pytest

from scripts.run_baselines import build_parser


def test_cli_defaults_to_reproducible_baseline_versions() -> None:
    arguments = build_parser().parse_args([])

    assert arguments.feature_version == "features-v1"
    assert arguments.target_version == "targets-v1"
    assert arguments.dataset_version == "dataset-v1"
    assert arguments.model_version == "baselines-v1"
    assert arguments.gap == 1


def test_cli_rejects_non_daily_timeframes() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--timeframe", "1H"])
