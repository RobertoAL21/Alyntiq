import logging
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.backtesting.engine import BacktestEngine
from app.backtesting.repository import BacktestDataError, BacktestDataset, load_backtest_dataset
from app.backtesting.types import BacktestConfig, BacktestResult
from app.strategies.baselines import BaselineStrategyParameters, build_baseline_strategies

logger = logging.getLogger(__name__)


class BaselineStrategyComparisonError(ValueError):
    """Raised when Phase 8 strategies cannot be compared on one historical dataset."""


@dataclass(frozen=True)
class BaselineStrategyRun:
    strategy_name: str
    result: BacktestResult


@dataclass(frozen=True)
class StrategyComparisonEntry:
    rank: int
    strategy_name: str
    total_return: float
    sharpe_ratio: float | None
    sortino_ratio: float | None
    max_drawdown: float
    number_of_trades: int


@dataclass(frozen=True)
class BaselineStrategyComparison:
    dataset: BacktestDataset
    config: BacktestConfig
    runs: tuple[BaselineStrategyRun, ...]
    leaderboard: tuple[StrategyComparisonEntry, ...]


class BaselineStrategyComparisonService:
    """Run every Phase 8 baseline over identical bars and execution-cost assumptions."""

    def run(
        self,
        session: Session,
        *,
        symbol: str,
        source: str,
        timeframe: str,
        start: date,
        end: date,
        config: BacktestConfig,
        strategy_parameters: BaselineStrategyParameters,
    ) -> BaselineStrategyComparison:
        try:
            dataset = load_backtest_dataset(
                session,
                symbol=symbol,
                source=source,
                timeframe=timeframe,
                start=start,
                end=end,
            )
        except BacktestDataError as error:
            raise BaselineStrategyComparisonError(str(error)) from error

        runs = tuple(
            BaselineStrategyRun(
                strategy_name=definition.name,
                result=BacktestEngine(config).run(dataset.bars, definition.strategy),
            )
            for definition in build_baseline_strategies(strategy_parameters)
        )
        leaderboard = build_strategy_leaderboard(runs)
        logger.info(
            "baseline_strategies_compared",
            extra={
                "symbol": dataset.symbol,
                "source": dataset.source,
                "timeframe": dataset.timeframe,
                "start": dataset.start.isoformat(),
                "end": dataset.end.isoformat(),
                "bar_count": len(dataset.bars),
                "strategy_count": len(runs),
            },
        )
        return BaselineStrategyComparison(
            dataset=dataset,
            config=config,
            runs=runs,
            leaderboard=leaderboard,
        )


def build_strategy_leaderboard(
    runs: tuple[BaselineStrategyRun, ...],
) -> tuple[StrategyComparisonEntry, ...]:
    """Rank baselines by total return while retaining risk and activity metrics for context."""
    ordered_runs = sorted(
        runs,
        key=lambda run: (run.result.metrics.total_return, run.strategy_name),
        reverse=True,
    )
    return tuple(
        StrategyComparisonEntry(
            rank=index,
            strategy_name=run.strategy_name,
            total_return=run.result.metrics.total_return,
            sharpe_ratio=run.result.metrics.sharpe_ratio,
            sortino_ratio=run.result.metrics.sortino_ratio,
            max_drawdown=run.result.metrics.max_drawdown,
            number_of_trades=run.result.metrics.number_of_trades,
        )
        for index, run in enumerate(ordered_runs, start=1)
    )
