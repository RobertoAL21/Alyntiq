import argparse
from datetime import date

import pytest

from scripts.ingest_market_data import build_parser, parse_date


def test_parse_date_accepts_iso_date() -> None:
    assert parse_date("2024-01-02") == date(2024, 1, 2)


def test_parse_date_rejects_non_iso_date() -> None:
    with pytest.raises(argparse.ArgumentTypeError, match="YYYY-MM-DD"):
        parse_date("01/02/2024")


def test_cli_limits_phase_one_to_daily_bars() -> None:
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "--symbol",
                "AAPL",
                "--start",
                "2024-01-02",
                "--end",
                "2024-01-03",
                "--timeframe",
                "1H",
            ]
        )
