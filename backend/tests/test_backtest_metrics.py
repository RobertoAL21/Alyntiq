from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.backtesting.metrics import calculate_backtest_metrics
from app.backtesting.types import BacktestConfig, EquityPoint, Trade


def test_metrics_calculates_equity_and_closed_trade_statistics() -> None:
    timestamp = datetime(2024, 1, 1, tzinfo=UTC)
    curve = (
        EquityPoint(timestamp, Decimal("100"), Decimal("0"), Decimal("100")),
        EquityPoint(timestamp + timedelta(days=1), Decimal("100"), Decimal("0"), Decimal("110")),
        EquityPoint(timestamp + timedelta(days=2), Decimal("100"), Decimal("0"), Decimal("99")),
    )
    trades = (
        Trade(
            "trade-000001",
            "AAPL",
            1,
            timestamp,
            timestamp + timedelta(days=1),
            Decimal("100"),
            Decimal("110"),
            Decimal("0"),
            Decimal("0"),
            Decimal("10"),
            Decimal("10"),
        ),
        Trade(
            "trade-000002",
            "AAPL",
            1,
            timestamp,
            timestamp + timedelta(days=2),
            Decimal("110"),
            Decimal("99"),
            Decimal("0"),
            Decimal("0"),
            Decimal("-11"),
            Decimal("-11"),
        ),
    )

    metrics = calculate_backtest_metrics(curve, trades, BacktestConfig(initial_cash=Decimal("100")))

    assert metrics.total_return == pytest.approx(-0.01)
    assert metrics.max_drawdown == pytest.approx(-0.1)
    assert metrics.number_of_trades == 2
    assert metrics.win_rate == 0.5
    assert metrics.profit_factor == pytest.approx(10 / 11)
    assert metrics.average_trade == -0.5
    assert metrics.best_trade == 10
    assert metrics.worst_trade == -11
    assert metrics.annualized_return is not None
    assert metrics.cagr is not None
    assert metrics.volatility is not None
    assert metrics.sharpe_ratio is not None
    assert metrics.sortino_ratio is not None
