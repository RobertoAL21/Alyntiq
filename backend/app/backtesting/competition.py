"""Fair, isolated historical competitions between supplied strategy factories."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from app.backtesting.engine import BacktestEngine
from app.backtesting.types import BacktestBar, BacktestConfig, BacktestResult, Strategy


class StrategyCompetitionError(ValueError):
    """Raised when competitors cannot be run under fair shared assumptions."""


@dataclass(frozen=True)
class StrategyCompetitor:
    """A named factory for one strategy's independent virtual portfolio run."""

    name: str
    strategy_factory: Callable[[], Strategy]


@dataclass(frozen=True)
class VirtualPortfolioRun:
    """The complete historical result for one independently initialized competitor."""

    strategy_name: str
    result: BacktestResult


@dataclass(frozen=True)
class StrategyCompetitionEntry:
    """A rank with return, risk, and activity context for one virtual portfolio."""

    rank: int
    strategy_name: str
    total_return: float
    sharpe_ratio: float | None
    sortino_ratio: float | None
    max_drawdown: float
    number_of_trades: int


@dataclass(frozen=True)
class StrategyCompetition:
    """Comparable strategy results sharing bars and explicit backtest assumptions."""

    config: BacktestConfig
    runs: tuple[VirtualPortfolioRun, ...]
    leaderboard: tuple[StrategyCompetitionEntry, ...]


class StrategyCompetitionService:
    """Run each supplied strategy against the same bars with isolated portfolios."""

    def run(
        self,
        bars: Sequence[BacktestBar],
        *,
        config: BacktestConfig,
        competitors: Sequence[StrategyCompetitor],
    ) -> StrategyCompetition:
        bars = tuple(bars)
        competitors = tuple(competitors)
        _validate_competitors(competitors)
        runs = tuple(
            VirtualPortfolioRun(
                strategy_name=competitor.name,
                result=BacktestEngine(config).run(bars, competitor.strategy_factory()),
            )
            for competitor in competitors
        )
        return StrategyCompetition(
            config=config,
            runs=runs,
            leaderboard=build_strategy_leaderboard(runs),
        )


def build_strategy_leaderboard(
    runs: Sequence[VirtualPortfolioRun],
) -> tuple[StrategyCompetitionEntry, ...]:
    """Rank portfolios by total return, retaining risk and trade-count context."""
    ordered_runs = sorted(
        runs,
        key=lambda run: (-run.result.metrics.total_return, run.strategy_name),
    )
    return tuple(
        StrategyCompetitionEntry(
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


def _validate_competitors(competitors: Sequence[StrategyCompetitor]) -> None:
    if not competitors:
        raise StrategyCompetitionError("at least one strategy competitor is required")
    names = []
    for competitor in competitors:
        if not competitor.name.strip():
            raise StrategyCompetitionError("strategy competitor names must not be blank")
        if not callable(competitor.strategy_factory):
            raise StrategyCompetitionError("strategy competitor factories must be callable")
        names.append(competitor.name.strip().casefold())
    if len(set(names)) != len(names):
        raise StrategyCompetitionError("strategy competitor names must be unique")
