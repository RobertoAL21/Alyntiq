from decimal import ROUND_FLOOR, Decimal

from app.portfolio.types import Portfolio, PortfolioValuation, PositionSize


class FixedPercentageSizer:
    """Calculate a whole-share buy quantity for a target percentage of marked equity."""

    def __init__(self, target_equity_pct: Decimal) -> None:
        if not Decimal("0") < target_equity_pct <= Decimal("1"):
            raise ValueError("target_equity_pct must be greater than zero and at most one")
        self._target_equity_pct = target_equity_pct

    def size(
        self,
        portfolio: Portfolio,
        valuation: PortfolioValuation,
        *,
        symbol: str,
        reference_price: Decimal,
    ) -> PositionSize:
        """Return an incremental buy size; it never creates a sell instruction or an order."""
        if not symbol.strip():
            raise ValueError("sizing symbol must not be blank")
        if reference_price <= 0:
            raise ValueError("sizing reference_price must be positive")
        normalized_symbol = symbol.strip().upper()
        current = valuation.position_for(normalized_symbol)
        if current is not None and current.market_price != reference_price:
            raise ValueError("reference_price must match the valuation price for an open position")
        current_notional = Decimal("0") if current is None else current.market_value
        target_notional = valuation.equity * self._target_equity_pct
        desired_notional = max(target_notional - current_notional, Decimal("0"))
        desired_quantity = _whole_shares(desired_notional / reference_price)
        affordable_quantity = _whole_shares(portfolio.cash / reference_price)
        quantity = min(desired_quantity, affordable_quantity)
        return PositionSize(
            symbol=normalized_symbol,
            target_equity_pct=self._target_equity_pct,
            target_notional=target_notional,
            current_notional=current_notional,
            quantity=quantity,
            limited_by_cash=affordable_quantity < desired_quantity,
        )


def _whole_shares(quantity: Decimal) -> int:
    return int(quantity.to_integral_value(rounding=ROUND_FLOOR))
