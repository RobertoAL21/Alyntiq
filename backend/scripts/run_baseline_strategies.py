import argparse
import json
from decimal import Decimal, InvalidOperation

from app.backtesting.service import (
    BaselineStrategyComparisonError,
    BaselineStrategyComparisonService,
)
from app.backtesting.types import BacktestConfig
from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.strategies.baselines import BaselineStrategyParameters
from scripts.ingest_market_data import parse_date


def parse_positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("value must be an integer") from error
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")
    return parsed


def parse_decimal(value: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation as error:
        raise argparse.ArgumentTypeError("value must be a decimal number") from error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare Phase 8 baseline strategies over one historical daily-bar period"
    )
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--start", required=True, type=parse_date)
    parser.add_argument("--end", required=True, type=parse_date)
    parser.add_argument("--source", default="alpaca:iex:raw")
    parser.add_argument("--timeframe", default="1D", choices=["1D"])
    parser.add_argument("--quantity", required=True, type=parse_positive_int)
    parser.add_argument("--initial-cash", default=Decimal("100000"), type=parse_decimal)
    parser.add_argument("--commission-rate", default=Decimal("0"), type=parse_decimal)
    parser.add_argument("--slippage-bps", default=Decimal("0"), type=parse_decimal)
    parser.add_argument("--fast-window", default=20, type=parse_positive_int)
    parser.add_argument("--slow-window", default=50, type=parse_positive_int)
    parser.add_argument("--rsi-window", default=14, type=parse_positive_int)
    parser.add_argument("--rsi-oversold", default=Decimal("30"), type=parse_decimal)
    parser.add_argument("--rsi-overbought", default=Decimal("70"), type=parse_decimal)
    parser.add_argument("--momentum-window", default=20, type=parse_positive_int)
    parser.add_argument("--random-seed", default=42, type=int)
    parser.add_argument("--random-action-probability", default=0.1, type=float)
    return parser


def main() -> int:
    parser = build_parser()
    arguments = parser.parse_args()
    if arguments.start > arguments.end:
        parser.error("--start must not be after --end")
    try:
        config = BacktestConfig(
            initial_cash=arguments.initial_cash,
            commission_rate=arguments.commission_rate,
            slippage_bps=arguments.slippage_bps,
        )
        strategy_parameters = BaselineStrategyParameters(
            quantity=arguments.quantity,
            fast_window=arguments.fast_window,
            slow_window=arguments.slow_window,
            rsi_window=arguments.rsi_window,
            rsi_oversold=arguments.rsi_oversold,
            rsi_overbought=arguments.rsi_overbought,
            momentum_window=arguments.momentum_window,
            random_seed=arguments.random_seed,
            random_action_probability=arguments.random_action_probability,
        )
    except ValueError as error:
        parser.error(str(error))

    configure_logging()
    try:
        with SessionLocal() as session:
            comparison = BaselineStrategyComparisonService().run(
                session,
                symbol=arguments.symbol,
                source=arguments.source,
                timeframe=arguments.timeframe,
                start=arguments.start,
                end=arguments.end,
                config=config,
                strategy_parameters=strategy_parameters,
            )
    except BaselineStrategyComparisonError as error:
        raise SystemExit(f"Baseline-strategy comparison failed: {error}") from error

    print(
        json.dumps(
            {
                "symbol": comparison.dataset.symbol,
                "source": comparison.dataset.source,
                "timeframe": comparison.dataset.timeframe,
                "start": comparison.dataset.start.isoformat(),
                "end": comparison.dataset.end.isoformat(),
                "bar_count": len(comparison.dataset.bars),
                "quantity": strategy_parameters.quantity,
                "commission_rate": str(config.commission_rate),
                "slippage_bps": str(config.slippage_bps),
                "leaderboard": [
                    {
                        "rank": entry.rank,
                        "strategy_name": entry.strategy_name,
                        "total_return": entry.total_return,
                        "sharpe_ratio": entry.sharpe_ratio,
                        "sortino_ratio": entry.sortino_ratio,
                        "max_drawdown": entry.max_drawdown,
                        "number_of_trades": entry.number_of_trades,
                    }
                    for entry in comparison.leaderboard
                ],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
