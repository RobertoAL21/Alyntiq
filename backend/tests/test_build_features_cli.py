import pytest

from scripts.build_features import build_parser


def test_cli_defaults_to_the_first_feature_version() -> None:
    arguments = build_parser().parse_args([])

    assert arguments.feature_version == "features-v1"
    assert arguments.source == "alpaca:iex:raw"
    assert arguments.timeframe == "1D"


def test_cli_limits_phase_three_to_daily_bars() -> None:
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["--timeframe", "1H"])
