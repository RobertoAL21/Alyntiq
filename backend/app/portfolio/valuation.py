from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal

from app.portfolio.types import Portfolio, PortfolioPosition, PortfolioValuation, PositionValuation


def mark_to_market(
    portfolio: Portfolio,
    prices: Mapping[str, Decimal],
    *,
    timestamp: datetime,
) -> PortfolioValuation:
    """Value every open long position at explicit completed market prices."""
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("portfolio valuation timestamps must include a timezone")
    normalized_prices = _normalize_prices(prices)
    missing_symbols = [
        position.symbol
        for position in portfolio.positions
        if position.symbol not in normalized_prices
    ]
    if missing_symbols:
        raise ValueError(f"missing market prices for open positions: {', '.join(missing_symbols)}")

    position_values = tuple(
        _position_valuation(position, normalized_prices[position.symbol])
        for position in portfolio.positions
    )
    total_market_value = sum((position.market_value for position in position_values), Decimal("0"))
    equity = portfolio.cash + total_market_value
    if equity <= 0:
        raise ValueError("portfolio equity must remain positive for exposure calculation")
    valued_positions = tuple(
        PositionValuation(
            symbol=position.symbol,
            quantity=position.quantity,
            market_price=position.market_price,
            market_value=position.market_value,
            unrealized_pnl=position.unrealized_pnl,
            exposure_pct=position.market_value / equity,
        )
        for position in position_values
    )
    return PortfolioValuation(
        timestamp=timestamp.astimezone(UTC),
        cash=portfolio.cash,
        equity=equity,
        realized_pnl=portfolio.realized_pnl,
        unrealized_pnl=sum(
            (position.unrealized_pnl for position in valued_positions), Decimal("0")
        ),
        gross_exposure_pct=total_market_value / equity,
        positions=valued_positions,
    )


def _position_valuation(position: PortfolioPosition, price: Decimal) -> PositionValuation:
    market_value = price * position.quantity
    return PositionValuation(
        symbol=position.symbol,
        quantity=position.quantity,
        market_price=price,
        market_value=market_value,
        unrealized_pnl=(price - position.average_entry_price) * position.quantity
        - position.entry_commission,
        exposure_pct=Decimal("0"),
    )


def _normalize_prices(prices: Mapping[str, Decimal]) -> dict[str, Decimal]:
    normalized: dict[str, Decimal] = {}
    for symbol, price in prices.items():
        normalized_symbol = symbol.strip().upper()
        if not normalized_symbol:
            raise ValueError("market-price symbol must not be blank")
        if price <= 0:
            raise ValueError("market prices must be positive")
        if normalized_symbol in normalized:
            raise ValueError("market-price symbols must be unique after normalization")
        normalized[normalized_symbol] = price
    return normalized
