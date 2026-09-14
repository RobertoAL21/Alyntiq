from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.backtesting.engine import BacktestEngine
from app.backtesting.types import BacktestBar, BacktestConfig, Portfolio, Signal, SignalSide
from app.risk.engine import RiskEngine
from app.risk.types import ProposedOrder, RiskContext, RiskLimits, RiskRule


def make_context(
    *,
    cash: str = "1000",
    equity: str = "1000",
    position_quantity: int = 0,
    average_entry_price: str | None = None,
    daily_realized_pnl: str = "0",
    current_drawdown: str = "0",
    filled_orders_today: int = 0,
) -> RiskContext:
    return RiskContext(
        timestamp=datetime(2024, 1, 2, tzinfo=UTC),
        symbol="AAPL",
        reference_price=Decimal("100"),
        equity=Decimal(equity),
        cash=Decimal(cash),
        position_quantity=position_quantity,
        average_entry_price=None if average_entry_price is None else Decimal(average_entry_price),
        daily_realized_pnl=Decimal(daily_realized_pnl),
        current_drawdown=Decimal(current_drawdown),
        filled_orders_today=filled_orders_today,
    )


def make_proposal(quantity: int = 10, side: SignalSide = SignalSide.BUY) -> ProposedOrder:
    return ProposedOrder(
        timestamp=datetime(2024, 1, 2, tzinfo=UTC),
        symbol="AAPL",
        side=side,
        quantity=quantity,
    )


def test_risk_engine_reduces_a_buy_to_all_shared_notional_and_cash_limits() -> None:
    engine = RiskEngine(
        RiskLimits(
            maximum_position_size_pct=Decimal("0.5"),
            maximum_portfolio_exposure=Decimal("0.3"),
            minimum_cash_reserve=Decimal("200"),
        )
    )

    decision = engine.evaluate(make_proposal(10), make_context(cash="400"))

    assert decision.approved is True
    assert decision.rule is RiskRule.MINIMUM_CASH_RESERVE
    assert decision.original_order.quantity == 10
    assert decision.modified_order is not None
    assert decision.modified_order.quantity == 2


def test_risk_engine_rejects_new_buys_at_loss_drawdown_and_trade_count_limits() -> None:
    proposal = make_proposal()
    daily_loss = RiskEngine(RiskLimits(maximum_daily_loss_pct=Decimal("0.05"))).evaluate(
        proposal, make_context(daily_realized_pnl="-60")
    )
    drawdown = RiskEngine(RiskLimits(maximum_drawdown_pct=Decimal("0.10"))).evaluate(
        proposal, make_context(current_drawdown="-0.11")
    )
    trade_count = RiskEngine(RiskLimits(max_trades_per_day=2)).evaluate(
        proposal, make_context(filled_orders_today=2)
    )

    assert daily_loss.approved is False
    assert daily_loss.rule is RiskRule.MAXIMUM_DAILY_LOSS
    assert drawdown.approved is False
    assert drawdown.rule is RiskRule.MAXIMUM_DRAWDOWN
    assert trade_count.approved is False
    assert trade_count.rule is RiskRule.MAX_TRADES_PER_DAY
    assert all(decision.modified_order is None for decision in (daily_loss, drawdown, trade_count))


def test_risk_engine_generates_stop_and_take_profit_exit_proposals() -> None:
    stop_engine = RiskEngine(RiskLimits(stop_loss_pct=Decimal("0.05")))
    take_engine = RiskEngine(RiskLimits(take_profit_pct=Decimal("0.10")))

    stop = stop_engine.evaluate_protection(
        make_context(position_quantity=3, average_entry_price="110")
    )
    take = take_engine.evaluate_protection(
        make_context(
            position_quantity=3,
            average_entry_price="90",
        )
    )

    assert stop is not None
    assert stop.rule is RiskRule.STOP_LOSS
    assert take is not None
    assert take.rule is RiskRule.TAKE_PROFIT
    assert take.modified_order is not None
    assert take.modified_order.side is SignalSide.SELL
    assert take.modified_order.quantity == 3


def make_bar(index: int, open_price: str, close_price: str | None = None) -> BacktestBar:
    value = Decimal(open_price)
    close = value if close_price is None else Decimal(close_price)
    return BacktestBar(
        timestamp=datetime(2024, 1, 2, tzinfo=UTC) + timedelta(days=index),
        symbol="AAPL",
        open=value,
        high=max(value, close) + Decimal("1"),
        low=min(value, close) - Decimal("1"),
        close=close,
    )


class BuyOnceStrategy:
    def on_bar(self, bar: BacktestBar, portfolio: Portfolio) -> Signal | None:
        if bar.timestamp == datetime(2024, 1, 2, tzinfo=UTC):
            return Signal(bar.timestamp, bar.symbol, SignalSide.BUY, 5)
        return None


def test_backtest_applies_risk_before_execution_and_generates_stop_exit() -> None:
    bars = (
        make_bar(0, "100"),
        make_bar(1, "100", close_price="90"),
        make_bar(2, "89"),
    )
    risk_engine = RiskEngine(
        RiskLimits(maximum_position_size_pct=Decimal("0.2"), stop_loss_pct=Decimal("0.05"))
    )

    result = BacktestEngine(
        BacktestConfig(initial_cash=Decimal("1000")), risk_engine=risk_engine
    ).run(bars, BuyOnceStrategy())

    assert [fill.quantity for fill in result.fills] == [2, 2]
    assert [fill.side for fill in result.fills] == [SignalSide.BUY, SignalSide.SELL]
    assert result.trades[0].exit_timestamp == bars[2].timestamp
