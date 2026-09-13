import pytest

from scripts.run_baseline_strategies import build_parser


def test_cli_requires_explicit_strategy_quantity_and_defaults_to_daily_bars() -> None:
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["--symbol", "AAPL", "--start", "2024-01-02", "--end", "2024-04-01"])

    arguments = parser.parse_args(
        [
            "--symbol",
            "AAPL",
            "--start",
            "2024-01-02",
            "--end",
            "2024-04-01",
            "--quantity",
            "10",
        ]
    )

    assert arguments.timeframe == "1D"
    assert arguments.quantity == 10
    assert arguments.random_seed == 42


def test_cli_rejects_invalid_strategy_quantity() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(
            [
                "--symbol",
                "AAPL",
                "--start",
                "2024-01-02",
                "--end",
                "2024-04-01",
                "--quantity",
                "0",
            ]
        )
