from dataclasses import dataclass
from decimal import Decimal

from app.portfolio.types import Portfolio, PortfolioFill, PortfolioPosition, PortfolioSide


class PortfolioAccountingError(ValueError):
    """Raised when a fill would violate multi-asset long-only portfolio accounting."""


@dataclass(frozen=True)
class FillApplication:
    portfolio: Portfolio
    realized_pnl: Decimal


def initial_portfolio(initial_cash: Decimal) -> Portfolio:
    return Portfolio(
        initial_cash=initial_cash,
        cash=initial_cash,
        positions=(),
        realized_pnl=Decimal("0"),
    )


def apply_fill(portfolio: Portfolio, fill: PortfolioFill) -> FillApplication:
    """Apply one executed fill without submitting orders or obtaining market prices."""
    if fill.side is PortfolioSide.BUY:
        return _apply_buy(portfolio, fill)
    return _apply_sell(portfolio, fill)


def _apply_buy(portfolio: Portfolio, fill: PortfolioFill) -> FillApplication:
    total_cost = fill.notional + fill.commission
    if total_cost > portfolio.cash:
        raise PortfolioAccountingError("insufficient cash for buy fill including commission")
    previous = portfolio.position_for(fill.symbol)
    previous_quantity = 0 if previous is None else previous.quantity
    previous_cost = (
        Decimal("0") if previous is None else previous.average_entry_price * previous.quantity
    )
    position = PortfolioPosition(
        symbol=fill.symbol,
        quantity=previous_quantity + fill.quantity,
        average_entry_price=(previous_cost + fill.notional) / (previous_quantity + fill.quantity),
        opened_at=fill.timestamp if previous is None else previous.opened_at,
        entry_commission=fill.commission
        if previous is None
        else previous.entry_commission + fill.commission,
    )
    return FillApplication(
        portfolio=Portfolio(
            initial_cash=portfolio.initial_cash,
            cash=portfolio.cash - total_cost,
            positions=_replace_position(portfolio.positions, fill.symbol, position),
            realized_pnl=portfolio.realized_pnl,
        ),
        realized_pnl=Decimal("0"),
    )


def _apply_sell(portfolio: Portfolio, fill: PortfolioFill) -> FillApplication:
    position = portfolio.position_for(fill.symbol)
    if position is None:
        raise PortfolioAccountingError("cannot sell a symbol without an open long position")
    if fill.quantity > position.quantity:
        raise PortfolioAccountingError("cannot sell more shares than the open long position")
    entry_commission = position.entry_commission * Decimal(fill.quantity) / position.quantity
    realized_pnl = (
        (fill.price - position.average_entry_price) * fill.quantity
        - entry_commission
        - fill.commission
    )
    remaining_quantity = position.quantity - fill.quantity
    positions = _replace_position(
        portfolio.positions,
        fill.symbol,
        None
        if remaining_quantity == 0
        else PortfolioPosition(
            symbol=position.symbol,
            quantity=remaining_quantity,
            average_entry_price=position.average_entry_price,
            opened_at=position.opened_at,
            entry_commission=position.entry_commission - entry_commission,
        ),
    )
    return FillApplication(
        portfolio=Portfolio(
            initial_cash=portfolio.initial_cash,
            cash=portfolio.cash + fill.notional - fill.commission,
            positions=positions,
            realized_pnl=portfolio.realized_pnl + realized_pnl,
        ),
        realized_pnl=realized_pnl,
    )


def _replace_position(
    positions: tuple[PortfolioPosition, ...],
    symbol: str,
    replacement: PortfolioPosition | None,
) -> tuple[PortfolioPosition, ...]:
    retained = tuple(position for position in positions if position.symbol != symbol)
    if replacement is not None:
        retained += (replacement,)
    return tuple(sorted(retained, key=lambda position: position.symbol))
