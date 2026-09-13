from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.backtesting.service import BaselineStrategyComparisonService
from app.backtesting.types import BacktestConfig
from app.market_data.repository import store_historical_bars
from app.market_data.schemas import HistoricalBar
from app.strategies.baselines import BaselineStrategyParameters


def test_runs_all_baselines_on_identical_bars_and_cost_assumptions(db_session: Session) -> None:
    start = date(2024, 1, 2)
    bars = []
    for index in range(80):
        timestamp = datetime(2024, 1, 2, tzinfo=UTC) + timedelta(days=index)
        close = Decimal("100") + Decimal(index % 10) - Decimal("5")
        bars.append(
            HistoricalBar(
                symbol="AAPL",
                timestamp=timestamp,
                open=close,
                high=close + Decimal("1"),
                low=close - Decimal("1"),
                close=close,
                volume=1_000,
                source="alpaca:iex:raw",
                timeframe="1D",
            )
        )
    store_historical_bars(db_session, bars)
    db_session.commit()
    config = BacktestConfig(
        initial_cash=Decimal("1000"),
        commission_rate=Decimal("0.001"),
        slippage_bps=Decimal("5"),
    )

    comparison = BaselineStrategyComparisonService().run(
        db_session,
        symbol="AAPL",
        source="alpaca:iex:raw",
        timeframe="1D",
        start=start,
        end=start + timedelta(days=79),
        config=config,
        strategy_parameters=BaselineStrategyParameters(quantity=1, random_seed=7),
    )

    assert len(comparison.dataset.bars) == 80
    assert [run.strategy_name for run in comparison.runs] == [
        "buy_and_hold",
        "moving_average_crossover",
        "rsi_mean_reversion",
        "momentum",
        "random",
    ]
    assert all(run.result.config == config for run in comparison.runs)
    assert all(len(run.result.equity_curve) == 80 for run in comparison.runs)
    assert {entry.strategy_name for entry in comparison.leaderboard} == {
        run.strategy_name for run in comparison.runs
    }
