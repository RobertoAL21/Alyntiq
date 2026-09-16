from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.backtesting.competition import (
    StrategyCompetitionError,
    StrategyCompetitionService,
    StrategyCompetitor,
)
from app.backtesting.types import BacktestBar, BacktestConfig, Portfolio, Signal
from app.strategies.baselines import BuyAndHoldStrategy


def make_bar(day: int, close: str) -> BacktestBar:
    price = Decimal(close)
    return BacktestBar(
        timestamp=datetime(2024, 1, 2, tzinfo=UTC) + timedelta(days=day),
        symbol="AAPL",
        open=price,
        high=price + Decimal("1"),
        low=price - Decimal("1"),
        close=price,
    )


class HoldStrategy:
    def on_bar(self, bar: BacktestBar, portfolio: Portfolio) -> Signal | None:
        return None


def test_competition_runs_fresh_strategies_with_independent_shared_capital() -> None:
    created: list[BuyAndHoldStrategy] = []

    def buy_and_hold() -> BuyAndHoldStrategy:
        strategy = BuyAndHoldStrategy(quantity=5)
        created.append(strategy)
        return strategy

    config = BacktestConfig(initial_cash=Decimal("100"))
    competition = StrategyCompetitionService().run(
        (make_bar(0, "10"), make_bar(1, "10"), make_bar(2, "15")),
        config=config,
        competitors=(
            StrategyCompetitor("buy_and_hold", buy_and_hold),
            StrategyCompetitor("hold", HoldStrategy),
        ),
    )

    buy_and_hold_run, hold_run = competition.runs

    assert len(created) == 1
    assert all(run.result.config == config for run in competition.runs)
    assert all(len(run.result.equity_curve) == 3 for run in competition.runs)
    assert buy_and_hold_run.result.portfolio.initial_cash == Decimal("100")
    assert hold_run.result.portfolio.initial_cash == Decimal("100")
    assert buy_and_hold_run.result.portfolio is not hold_run.result.portfolio
    assert buy_and_hold_run.result.metrics.total_return == 0.25
    assert hold_run.result.metrics.total_return == 0
    assert [entry.strategy_name for entry in competition.leaderboard] == ["buy_and_hold", "hold"]
    assert [entry.rank for entry in competition.leaderboard] == [1, 2]


@pytest.mark.parametrize(
    "competitors, message",
    [
        ((), "at least one"),
        ((StrategyCompetitor("", HoldStrategy),), "must not be blank"),
        (
            (
                StrategyCompetitor("momentum", HoldStrategy),
                StrategyCompetitor("MOMENTUM", HoldStrategy),
            ),
            "must be unique",
        ),
    ],
)
def test_competition_rejects_ambiguous_competitors(
    competitors: tuple[StrategyCompetitor, ...], message: str
) -> None:
    with pytest.raises(StrategyCompetitionError, match=message):
        StrategyCompetitionService().run(
            (make_bar(0, "10"),),
            config=BacktestConfig(),
            competitors=competitors,
        )
