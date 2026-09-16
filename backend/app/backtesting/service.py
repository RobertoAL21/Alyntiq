import logging
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.backtesting.competition import (
    StrategyCompetitionEntry,
    StrategyCompetitionService,
    StrategyCompetitor,
    VirtualPortfolioRun,
)
from app.backtesting.competition import build_strategy_leaderboard as _build_strategy_leaderboard
from app.backtesting.repository import BacktestDataError, BacktestDataset, load_backtest_dataset
from app.backtesting.types import BacktestConfig
from app.strategies.baselines import BaselineStrategyParameters, build_baseline_strategies

logger = logging.getLogger(__name__)


class BaselineStrategyComparisonError(ValueError):
    """Raised when Phase 8 strategies cannot be compared on one historical dataset."""


BaselineStrategyRun = VirtualPortfolioRun
StrategyComparisonEntry = StrategyCompetitionEntry
build_strategy_leaderboard = _build_strategy_leaderboard


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

        competition = StrategyCompetitionService().run(
            dataset.bars,
            config=config,
            competitors=tuple(
                StrategyCompetitor(definition.name, definition.strategy_factory)
                for definition in build_baseline_strategies(strategy_parameters)
            ),
        )
        logger.info(
            "baseline_strategies_compared",
            extra={
                "symbol": dataset.symbol,
                "source": dataset.source,
                "timeframe": dataset.timeframe,
                "start": dataset.start.isoformat(),
                "end": dataset.end.isoformat(),
                "bar_count": len(dataset.bars),
                "strategy_count": len(competition.runs),
            },
        )
        return BaselineStrategyComparison(
            dataset=dataset,
            config=config,
            runs=competition.runs,
            leaderboard=competition.leaderboard,
        )
