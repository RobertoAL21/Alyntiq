import math
import statistics
from collections.abc import Sequence

from app.backtesting.types import BacktestConfig, BacktestMetrics, EquityPoint, Trade


def calculate_backtest_metrics(
    equity_curve: Sequence[EquityPoint],
    trades: Sequence[Trade],
    config: BacktestConfig,
) -> BacktestMetrics:
    """Calculate documented historical research metrics with a zero risk-free rate."""
    equities = [float(point.equity) for point in equity_curve]
    returns = [
        current / previous - 1 for previous, current in zip(equities, equities[1:], strict=False)
    ]
    total_return = equities[-1] / float(config.initial_cash) - 1
    annualized_return = None
    cagr = None
    volatility = None
    sharpe_ratio = None
    sortino_ratio = None
    if returns:
        annualized_return = statistics.fmean(returns) * config.trading_days_per_year
        periods = len(returns)
        cagr = (equities[-1] / float(config.initial_cash)) ** (
            config.trading_days_per_year / periods
        ) - 1
    if len(returns) > 1:
        volatility = statistics.stdev(returns) * math.sqrt(config.trading_days_per_year)
        if volatility > 0 and annualized_return is not None:
            sharpe_ratio = annualized_return / volatility
        downside_deviation = math.sqrt(
            statistics.fmean(min(value, 0) ** 2 for value in returns)
        ) * math.sqrt(config.trading_days_per_year)
        if downside_deviation > 0 and annualized_return is not None:
            sortino_ratio = annualized_return / downside_deviation

    max_drawdown = _maximum_drawdown(equities)
    trade_pnls = [float(trade.net_pnl) for trade in trades]
    winners = [pnl for pnl in trade_pnls if pnl > 0]
    losers = [pnl for pnl in trade_pnls if pnl < 0]
    profit_factor = None if not losers else sum(winners) / abs(sum(losers))
    return BacktestMetrics(
        total_return=total_return,
        annualized_return=annualized_return,
        cagr=cagr,
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=sortino_ratio,
        max_drawdown=max_drawdown,
        volatility=volatility,
        win_rate=None if not trade_pnls else len(winners) / len(trade_pnls),
        profit_factor=profit_factor,
        number_of_trades=len(trade_pnls),
        average_trade=None if not trade_pnls else statistics.fmean(trade_pnls),
        best_trade=None if not trade_pnls else max(trade_pnls),
        worst_trade=None if not trade_pnls else min(trade_pnls),
    )


def _maximum_drawdown(equities: Sequence[float]) -> float:
    peak = equities[0]
    maximum_drawdown = 0.0
    for equity in equities:
        peak = max(peak, equity)
        maximum_drawdown = min(maximum_drawdown, equity / peak - 1)
    return maximum_drawdown
