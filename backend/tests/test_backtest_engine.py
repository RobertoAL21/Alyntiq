from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.backtesting.engine import BacktestEngine, BacktestInputError
from app.backtesting.types import (
    BacktestBar,
    BacktestConfig,
    OrderStatus,
    Portfolio,
    Signal,
    SignalSide,
)


def make_bar(day: int, *, open_price: str, close_price: str, symbol: str = "AAPL") -> BacktestBar:
    timestamp = datetime(2024, 1, 1, tzinfo=UTC) + timedelta(days=day)
    open_value = Decimal(open_price)
    close_value = Decimal(close_price)
    return BacktestBar(
        timestamp=timestamp,
        symbol=symbol,
        open=open_value,
        high=max(open_value, close_value) + Decimal("1"),
        low=min(open_value, close_value) - Decimal("1"),
        close=close_value,
    )


class ScheduledSignals:
    def __init__(self, signals: dict[datetime, Signal]) -> None:
        self._signals = signals

    def on_bar(self, bar: BacktestBar, portfolio: Portfolio) -> Signal | None:
        return self._signals.get(bar.timestamp)


def test_backtest_fills_a_close_generated_signal_at_the_next_open_with_costs() -> None:
    bars = (
        make_bar(0, open_price="100", close_price="101"),
        make_bar(1, open_price="110", close_price="112"),
        make_bar(2, open_price="120", close_price="121"),
    )
    strategy = ScheduledSignals(
        {
            bars[0].timestamp: Signal(bars[0].timestamp, "AAPL", SignalSide.BUY, 10),
            bars[1].timestamp: Signal(bars[1].timestamp, "AAPL", SignalSide.SELL, 10),
        }
    )
    result = BacktestEngine(
        BacktestConfig(
            initial_cash=Decimal("2000"),
            commission_rate=Decimal("0.01"),
            slippage_bps=Decimal("10"),
        )
    ).run(bars, strategy)

    assert [fill.timestamp for fill in result.fills] == [bars[1].timestamp, bars[2].timestamp]
    assert [fill.price for fill in result.fills] == [Decimal("110.110"), Decimal("119.880")]
    assert [fill.commission for fill in result.fills] == [Decimal("11.01100"), Decimal("11.98800")]
    assert result.orders[0].status is OrderStatus.FILLED
    assert result.orders[1].status is OrderStatus.FILLED
    assert result.trades[0].net_pnl == Decimal("74.70100")
    assert result.portfolio.cash == Decimal("2074.70100")
    assert result.portfolio.position is None
    assert result.metrics.number_of_trades == 1


def test_backtest_cancels_a_last_bar_signal_and_never_uses_a_same_bar_fill() -> None:
    bar = make_bar(0, open_price="100", close_price="105")
    strategy = ScheduledSignals({bar.timestamp: Signal(bar.timestamp, "AAPL", SignalSide.BUY, 1)})

    result = BacktestEngine().run((bar,), strategy)

    assert result.fills == ()
    assert result.orders[0].status is OrderStatus.CANCELLED
    assert result.equity_curve[0].equity == Decimal("100000")


def test_backtest_rejects_orders_that_break_long_only_cash_accounting() -> None:
    bars = (
        make_bar(0, open_price="100", close_price="100"),
        make_bar(1, open_price="100", close_price="100"),
    )
    strategy = ScheduledSignals(
        {bars[0].timestamp: Signal(bars[0].timestamp, "AAPL", SignalSide.BUY, 2)}
    )

    result = BacktestEngine(BacktestConfig(initial_cash=Decimal("100"))).run(bars, strategy)

    assert result.fills == ()
    assert result.orders[0].status is OrderStatus.REJECTED
    assert result.portfolio.cash == Decimal("100")
    assert result.portfolio.position is None


def test_backtest_rejects_unordered_or_multi_symbol_data() -> None:
    first = make_bar(1, open_price="100", close_price="100")
    earlier = make_bar(0, open_price="100", close_price="100")
    strategy = ScheduledSignals({})

    with pytest.raises(BacktestInputError, match="strictly increasing"):
        BacktestEngine().run((first, earlier), strategy)

    with pytest.raises(BacktestInputError, match="one symbol"):
        BacktestEngine().run(
            (earlier, make_bar(1, open_price="100", close_price="100", symbol="MSFT")), strategy
        )
