from dataclasses import replace
from decimal import ROUND_FLOOR, Decimal

from app.backtesting.types import SignalSide
from app.observability.telemetry import get_telemetry
from app.risk.types import ProposedOrder, RiskContext, RiskDecision, RiskLimits, RiskRule


class RiskEngine:
    """Evaluate strategy proposals without training models, placing orders, or mutating state."""

    def __init__(self, limits: RiskLimits) -> None:
        self._limits = limits

    def evaluate(self, proposal: ProposedOrder, context: RiskContext) -> RiskDecision:
        """Approve, reject, or reduce a proposed order using only the supplied current context."""
        _validate_identity(proposal, context)
        if proposal.side is SignalSide.SELL:
            return _approved(proposal)
        rejection = self._buy_rejection(proposal, context)
        if rejection is not None:
            get_telemetry().record_rejected_trade(reason=rejection.rule.value)
            return rejection
        decision = self._limit_buy_quantity(proposal, context)
        if not decision.approved:
            assert decision.rule is not None
            get_telemetry().record_rejected_trade(reason=decision.rule.value)
        return decision

    def evaluate_protection(self, context: RiskContext) -> RiskDecision | None:
        """Create an approved risk-exit proposal when a configured stop or take-profit triggers."""
        if context.position_quantity == 0:
            return None
        assert context.average_entry_price is not None
        proposal = ProposedOrder(
            timestamp=context.timestamp,
            symbol=context.symbol,
            side=SignalSide.SELL,
            quantity=context.position_quantity,
        )
        if self._limits.stop_loss_pct is not None:
            stop_price = context.average_entry_price * (Decimal("1") - self._limits.stop_loss_pct)
            if context.reference_price <= stop_price:
                return RiskDecision(
                    approved=True,
                    reason="stop-loss threshold triggered",
                    rule=RiskRule.STOP_LOSS,
                    original_order=proposal,
                    modified_order=proposal,
                )
        if self._limits.take_profit_pct is not None:
            take_profit_price = context.average_entry_price * (
                Decimal("1") + self._limits.take_profit_pct
            )
            if context.reference_price >= take_profit_price:
                return RiskDecision(
                    approved=True,
                    reason="take-profit threshold triggered",
                    rule=RiskRule.TAKE_PROFIT,
                    original_order=proposal,
                    modified_order=proposal,
                )
        return None

    def _buy_rejection(self, proposal: ProposedOrder, context: RiskContext) -> RiskDecision | None:
        if self._limits.maximum_daily_loss_pct is not None and context.daily_realized_pnl <= -(
            context.equity * self._limits.maximum_daily_loss_pct
        ):
            return _rejected(
                proposal,
                RiskRule.MAXIMUM_DAILY_LOSS,
                "maximum daily realized-loss limit reached",
            )
        if (
            self._limits.maximum_drawdown_pct is not None
            and context.current_drawdown <= -self._limits.maximum_drawdown_pct
        ):
            return _rejected(
                proposal,
                RiskRule.MAXIMUM_DRAWDOWN,
                "maximum drawdown limit reached",
            )
        if (
            self._limits.max_trades_per_day is not None
            and context.filled_orders_today >= self._limits.max_trades_per_day
        ):
            return _rejected(
                proposal,
                RiskRule.MAX_TRADES_PER_DAY,
                "maximum filled-order count for the day reached",
            )
        return None

    def _limit_buy_quantity(self, proposal: ProposedOrder, context: RiskContext) -> RiskDecision:
        quantity = proposal.quantity
        limiting_rule: RiskRule | None = None
        for rule, limit in (
            (RiskRule.MAXIMUM_POSITION_SIZE, self._limits.maximum_position_size_pct),
            (RiskRule.MAXIMUM_PORTFOLIO_EXPOSURE, self._limits.maximum_portfolio_exposure),
        ):
            if limit is None:
                continue
            maximum_quantity = _maximum_buy_quantity_for_fraction(limit, context)
            if maximum_quantity < quantity:
                quantity = maximum_quantity
                limiting_rule = rule
        if self._limits.minimum_cash_reserve is not None:
            maximum_quantity = _maximum_buy_quantity_for_cash_reserve(
                self._limits.minimum_cash_reserve, context
            )
            if maximum_quantity < quantity:
                quantity = maximum_quantity
                limiting_rule = RiskRule.MINIMUM_CASH_RESERVE
        if quantity < 1:
            assert limiting_rule is not None
            return _rejected(
                proposal, limiting_rule, "risk limit leaves no purchasable whole shares"
            )
        if quantity == proposal.quantity:
            return _approved(proposal)
        modified_order = replace(proposal, quantity=quantity)
        assert limiting_rule is not None
        return RiskDecision(
            approved=True,
            reason="quantity reduced to comply with risk limit",
            rule=limiting_rule,
            original_order=proposal,
            modified_order=modified_order,
        )


def _validate_identity(proposal: ProposedOrder, context: RiskContext) -> None:
    if proposal.timestamp != context.timestamp:
        raise ValueError("proposed order timestamp must match risk context timestamp")
    if proposal.symbol != context.symbol:
        raise ValueError("proposed order symbol must match risk context symbol")


def _maximum_buy_quantity_for_fraction(limit: Decimal, context: RiskContext) -> int:
    maximum_total_quantity = int(
        (context.equity * limit / context.reference_price).to_integral_value(rounding=ROUND_FLOOR)
    )
    return maximum_total_quantity - context.position_quantity


def _maximum_buy_quantity_for_cash_reserve(reserve: Decimal, context: RiskContext) -> int:
    return int(
        ((context.cash - reserve) / context.reference_price).to_integral_value(rounding=ROUND_FLOOR)
    )


def _approved(proposal: ProposedOrder) -> RiskDecision:
    return RiskDecision(
        approved=True,
        reason="approved",
        rule=None,
        original_order=proposal,
        modified_order=proposal,
    )


def _rejected(proposal: ProposedOrder, rule: RiskRule, reason: str) -> RiskDecision:
    return RiskDecision(
        approved=False,
        reason=reason,
        rule=rule,
        original_order=proposal,
        modified_order=None,
    )
