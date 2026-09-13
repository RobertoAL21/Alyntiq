from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.backtesting.portfolio import initial_portfolio
from app.backtesting.types import BacktestBar, SignalSide
from app.strategies.baselines import (
    BaselineStrategyParameters,
    BuyAndHoldStrategy,
    MomentumStrategy,
    MovingAverageCrossoverStrategy,
    RandomStrategy,
    RsiMeanReversionStrategy,
    build_baseline_strategies,
)


def make_bar(index: int, close: str) -> BacktestBar:
    value = Decimal(close)
    return BacktestBar(
        timestamp=datetime(2024, 1, 2, tzinfo=UTC) + timedelta(days=index),
        symbol="AAPL",
        open=value,
        high=value + Decimal("1"),
        low=value - Decimal("1"),
        close=value,
    )


def test_baseline_builder_provides_every_phase_eight_strategy() -> None:
    strategies = build_baseline_strategies(BaselineStrategyParameters(quantity=1))

    assert [strategy.name for strategy in strategies] == [
        "buy_and_hold",
        "moving_average_crossover",
        "rsi_mean_reversion",
        "momentum",
        "random",
    ]


def test_buy_and_hold_submits_only_one_buy_signal() -> None:
    strategy = BuyAndHoldStrategy(quantity=2)
    portfolio = initial_portfolio(Decimal("1000"))

    first_signal = strategy.on_bar(make_bar(0, "100"), portfolio)

    assert first_signal is not None
    assert first_signal.side is SignalSide.BUY
    assert first_signal.quantity == 2
    assert strategy.on_bar(make_bar(1, "101"), portfolio) is None


def test_indicator_strategies_use_only_current_and_prior_closes() -> None:
    portfolio = initial_portfolio(Decimal("1000"))
    moving_average = MovingAverageCrossoverStrategy(quantity=1, fast_window=2, slow_window=3)
    rsi = RsiMeanReversionStrategy(
        quantity=1,
        window=2,
        oversold=Decimal("30"),
        overbought=Decimal("70"),
    )
    momentum = MomentumStrategy(quantity=1, window=2)

    moving_average_signals = [
        moving_average.on_bar(make_bar(index, close), portfolio)
        for index, close in enumerate(["13", "12", "11", "15"])
    ]
    rsi_signals = [
        rsi.on_bar(make_bar(index, close), portfolio)
        for index, close in enumerate(["13", "12", "11"])
    ]
    momentum_signals = [
        momentum.on_bar(make_bar(index, close), portfolio)
        for index, close in enumerate(["11", "12", "13"])
    ]

    assert moving_average_signals[:-1] == [None, None, None]
    assert moving_average_signals[-1] is not None
    assert moving_average_signals[-1].side is SignalSide.BUY
    assert rsi_signals[:2] == [None, None]
    assert rsi_signals[-1] is not None
    assert rsi_signals[-1].side is SignalSide.BUY
    assert momentum_signals[:2] == [None, None]
    assert momentum_signals[-1] is not None
    assert momentum_signals[-1].side is SignalSide.BUY


def test_random_strategy_is_seeded_and_reproducible() -> None:
    first = RandomStrategy(quantity=1, seed=17, action_probability=0.5)
    second = RandomStrategy(quantity=1, seed=17, action_probability=0.5)
    portfolio = initial_portfolio(Decimal("1000"))
    bars = [make_bar(index, str(100 + index)) for index in range(8)]

    first_outputs = [first.on_bar(bar, portfolio) for bar in bars]
    second_outputs = [second.on_bar(bar, portfolio) for bar in bars]

    assert first_outputs == second_outputs
