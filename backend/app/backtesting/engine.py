from collections.abc import Sequence
from dataclasses import replace
from decimal import Decimal

from app.backtesting.metrics import calculate_backtest_metrics
from app.backtesting.portfolio import PortfolioAccountingError, apply_fill, initial_portfolio
from app.backtesting.types import (
    BacktestBar,
    BacktestConfig,
    BacktestResult,
    EquityPoint,
    Fill,
    Order,
    OrderStatus,
    Portfolio,
    Signal,
    SignalSide,
    Strategy,
    Trade,
)
from app.risk.engine import RiskEngine
from app.risk.types import ProposedOrder, RiskContext


class BacktestInputError(ValueError):
    """Raised when historical bars or strategy output cannot form a valid backtest."""


class BacktestEngine:
    """Run a single-symbol, long-only historical simulation without same-bar look-ahead."""

    def __init__(
        self,
        config: BacktestConfig | None = None,
        risk_engine: RiskEngine | None = None,
    ) -> None:
        self._config = config or BacktestConfig()
        self._risk_engine = risk_engine

    def run(self, bars: Sequence[BacktestBar], strategy: Strategy) -> BacktestResult:
        bars = tuple(bars)
        _validate_bars(bars)
        portfolio = initial_portfolio(self._config.initial_cash)
        orders: list[Order] = []
        fills: list[Fill] = []
        trades: list[Trade] = []
        equity_curve: list[EquityPoint] = []
        pending_order_index: int | None = None

        for bar in bars:
            if pending_order_index is not None:
                portfolio, fill, trade, rejection_reason = self._execute_pending_order(
                    orders[pending_order_index], bar, portfolio, len(fills) + 1, len(trades) + 1
                )
                if rejection_reason is None:
                    orders[pending_order_index] = replace(
                        orders[pending_order_index], status=OrderStatus.FILLED
                    )
                    fills.append(fill)
                    if trade is not None:
                        trades.append(trade)
                else:
                    orders[pending_order_index] = replace(
                        orders[pending_order_index],
                        status=OrderStatus.REJECTED,
                        rejection_reason=rejection_reason,
                    )
                pending_order_index = None

            equity_curve.append(_equity_point(portfolio, bar))
            proposal = self._risk_protection_proposal(portfolio, bar, equity_curve, fills, trades)
            if proposal is None:
                signal = strategy.on_bar(bar, portfolio)
                if signal is not None:
                    _validate_signal(signal, bar)
                    proposal = ProposedOrder(
                        timestamp=signal.timestamp,
                        symbol=signal.symbol,
                        side=signal.side,
                        quantity=signal.quantity,
                        lineage=signal.lineage,
                    )
                    proposal = self._risk_approved_proposal(
                        proposal, portfolio, bar, equity_curve, fills, trades
                    )
            if proposal is not None:
                orders.append(
                    Order(
                        id=f"order-{len(orders) + 1:06d}",
                        created_at=proposal.timestamp,
                        symbol=proposal.symbol,
                        side=proposal.side,
                        quantity=proposal.quantity,
                        status=OrderStatus.PENDING,
                        lineage=proposal.lineage,
                    )
                )
                pending_order_index = len(orders) - 1

        if pending_order_index is not None:
            orders[pending_order_index] = replace(
                orders[pending_order_index],
                status=OrderStatus.CANCELLED,
                rejection_reason="no subsequent market bar is available for execution",
            )
        return BacktestResult(
            config=self._config,
            portfolio=portfolio,
            orders=tuple(orders),
            fills=tuple(fills),
            trades=tuple(trades),
            equity_curve=tuple(equity_curve),
            metrics=calculate_backtest_metrics(equity_curve, trades, self._config),
        )

    def _execute_pending_order(
        self,
        order: Order,
        bar: BacktestBar,
        portfolio: Portfolio,
        fill_number: int,
        trade_number: int,
    ) -> tuple[Portfolio, Fill | None, Trade | None, str | None]:
        fill_price = _slipped_open_price(bar.open, order.side, self._config.slippage_bps)
        commission = fill_price * order.quantity * self._config.commission_rate
        fill = Fill(
            id=f"fill-{fill_number:06d}",
            order_id=order.id,
            timestamp=bar.timestamp,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            commission=commission,
            lineage=order.lineage,
        )
        try:
            application = apply_fill(portfolio, fill, trade_id=f"trade-{trade_number:06d}")
        except PortfolioAccountingError as error:
            return portfolio, None, None, str(error)
        return application.portfolio, fill, application.trade, None

    def _risk_protection_proposal(
        self,
        portfolio: Portfolio,
        bar: BacktestBar,
        equity_curve: list[EquityPoint],
        fills: list[Fill],
        trades: list[Trade],
    ) -> ProposedOrder | None:
        if self._risk_engine is None:
            return None
        decision = self._risk_engine.evaluate_protection(
            _risk_context(portfolio, bar, equity_curve, fills, trades)
        )
        return None if decision is None else decision.modified_order

    def _risk_approved_proposal(
        self,
        proposal: ProposedOrder,
        portfolio: Portfolio,
        bar: BacktestBar,
        equity_curve: list[EquityPoint],
        fills: list[Fill],
        trades: list[Trade],
    ) -> ProposedOrder | None:
        if self._risk_engine is None:
            return proposal
        decision = self._risk_engine.evaluate(
            proposal,
            _risk_context(portfolio, bar, equity_curve, fills, trades),
        )
        return decision.modified_order if decision.approved else None


def _validate_bars(bars: Sequence[BacktestBar]) -> None:
    if not bars:
        raise BacktestInputError("at least one historical bar is required")
    symbols = {bar.symbol for bar in bars}
    if len(symbols) != 1:
        raise BacktestInputError("Phase 7 backtests support exactly one symbol")
    if any(
        current.timestamp <= previous.timestamp
        for previous, current in zip(bars, bars[1:], strict=False)
    ):
        raise BacktestInputError("historical bars must be in strictly increasing timestamp order")


def _validate_signal(signal: Signal, bar: BacktestBar) -> None:
    if signal.timestamp != bar.timestamp:
        raise BacktestInputError("strategy signals must use the current completed-bar timestamp")
    if signal.symbol != bar.symbol:
        raise BacktestInputError("strategy signal symbol must match the backtest symbol")


def _slipped_open_price(open_price: Decimal, side: SignalSide, slippage_bps: Decimal) -> Decimal:
    adjustment = slippage_bps / Decimal("10000")
    return open_price * (
        Decimal("1") + adjustment if side is SignalSide.BUY else Decimal("1") - adjustment
    )


def _equity_point(portfolio: Portfolio, bar: BacktestBar) -> EquityPoint:
    position_market_value = (
        Decimal("0") if portfolio.position is None else portfolio.position.quantity * bar.close
    )
    return EquityPoint(
        timestamp=bar.timestamp,
        cash=portfolio.cash,
        position_market_value=position_market_value,
        equity=portfolio.cash + position_market_value,
    )


def _risk_context(
    portfolio: Portfolio,
    bar: BacktestBar,
    equity_curve: list[EquityPoint],
    fills: list[Fill],
    trades: list[Trade],
) -> RiskContext:
    position = portfolio.position
    current_equity = equity_curve[-1].equity
    peak_equity = max(point.equity for point in equity_curve)
    today = bar.timestamp.date()
    return RiskContext(
        timestamp=bar.timestamp,
        symbol=bar.symbol,
        reference_price=bar.close,
        equity=current_equity,
        cash=portfolio.cash,
        position_quantity=0 if position is None else position.quantity,
        average_entry_price=None if position is None else position.average_entry_price,
        daily_realized_pnl=sum(
            (trade.net_pnl for trade in trades if trade.exit_timestamp.date() == today),
            Decimal("0"),
        ),
        current_drawdown=current_equity / peak_equity - Decimal("1"),
        filled_orders_today=sum(1 for fill in fills if fill.timestamp.date() == today),
    )
