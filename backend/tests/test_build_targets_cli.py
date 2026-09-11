import pytest

from scripts.build_targets import build_parser


def test_cli_defaults_to_the_first_target_version() -> None:
    arguments = build_parser().parse_args([])

    assert arguments.target_version == "targets-v1"
    assert arguments.source == "alpaca:iex:raw"
    assert arguments.timeframe == "1D"


def test_cli_limits_phase_four_to_daily_bars() -> None:
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["--timeframe", "1H"])
