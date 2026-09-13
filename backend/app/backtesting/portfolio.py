from dataclasses import dataclass
from decimal import Decimal

from app.backtesting.types import Fill, Portfolio, Position, SignalSide, Trade


class PortfolioAccountingError(ValueError):
    """Raised when a simulated fill would violate long-only cash or position accounting."""


@dataclass(frozen=True)
class FillApplication:
    portfolio: Portfolio
    trade: Trade | None


def initial_portfolio(initial_cash: Decimal) -> Portfolio:
    return Portfolio(
        initial_cash=initial_cash,
        cash=initial_cash,
        position=None,
        realized_pnl=Decimal("0"),
    )


def apply_fill(portfolio: Portfolio, fill: Fill, *, trade_id: str) -> FillApplication:
    """Apply a long-only fill, allocating entry costs to a closed trade when selling."""
    if fill.side is SignalSide.BUY:
        return _apply_buy(portfolio, fill)
    return _apply_sell(portfolio, fill, trade_id=trade_id)


def _apply_buy(portfolio: Portfolio, fill: Fill) -> FillApplication:
    total_cost = fill.notional + fill.commission
    if total_cost > portfolio.cash:
        raise PortfolioAccountingError("insufficient cash for buy order including commission")
    if portfolio.position is not None and portfolio.position.symbol != fill.symbol:
        raise PortfolioAccountingError("Phase 7 backtests support one symbol only")

    previous = portfolio.position
    previous_quantity = 0 if previous is None else previous.quantity
    previous_cost = (
        Decimal("0") if previous is None else previous.average_entry_price * previous.quantity
    )
    new_quantity = previous_quantity + fill.quantity
    position = Position(
        symbol=fill.symbol,
        quantity=new_quantity,
        average_entry_price=(previous_cost + fill.notional) / new_quantity,
        opened_at=fill.timestamp if previous is None else previous.opened_at,
        entry_commission=fill.commission
        if previous is None
        else previous.entry_commission + fill.commission,
    )
    return FillApplication(
        portfolio=Portfolio(
            initial_cash=portfolio.initial_cash,
            cash=portfolio.cash - total_cost,
            position=position,
            realized_pnl=portfolio.realized_pnl,
        ),
        trade=None,
    )


def _apply_sell(portfolio: Portfolio, fill: Fill, *, trade_id: str) -> FillApplication:
    position = portfolio.position
    if position is None or position.symbol != fill.symbol:
        raise PortfolioAccountingError("cannot sell a symbol without an open position")
    if fill.quantity > position.quantity:
        raise PortfolioAccountingError("cannot sell more shares than the open long position")

    entry_commission = position.entry_commission * Decimal(fill.quantity) / position.quantity
    gross_pnl = (fill.price - position.average_entry_price) * fill.quantity
    net_pnl = gross_pnl - entry_commission - fill.commission
    remaining_quantity = position.quantity - fill.quantity
    remaining_position = (
        None
        if remaining_quantity == 0
        else Position(
            symbol=position.symbol,
            quantity=remaining_quantity,
            average_entry_price=position.average_entry_price,
            opened_at=position.opened_at,
            entry_commission=position.entry_commission - entry_commission,
        )
    )
    trade = Trade(
        id=trade_id,
        symbol=fill.symbol,
        quantity=fill.quantity,
        entry_timestamp=position.opened_at,
        exit_timestamp=fill.timestamp,
        entry_price=position.average_entry_price,
        exit_price=fill.price,
        entry_commission=entry_commission,
        exit_commission=fill.commission,
        gross_pnl=gross_pnl,
        net_pnl=net_pnl,
    )
    return FillApplication(
        portfolio=Portfolio(
            initial_cash=portfolio.initial_cash,
            cash=portfolio.cash + fill.notional - fill.commission,
            position=remaining_position,
            realized_pnl=portfolio.realized_pnl + net_pnl,
        ),
        trade=trade,
    )
