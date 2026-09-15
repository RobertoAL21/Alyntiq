from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.portfolio import (
    FixedPercentageSizer,
    PortfolioAccountingError,
    PortfolioFill,
    PortfolioSide,
    apply_fill,
    initial_portfolio,
    mark_to_market,
)


def timestamp(day: int = 0) -> datetime:
    return datetime(2024, 1, 2, tzinfo=UTC) + timedelta(days=day)


def fill(
    identifier: str,
    symbol: str,
    side: PortfolioSide,
    quantity: int,
    price: str,
    commission: str = "0",
) -> PortfolioFill:
    return PortfolioFill(
        id=identifier,
        timestamp=timestamp(),
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=Decimal(price),
        commission=Decimal(commission),
    )


def test_multi_asset_valuation_reports_cash_equity_pnl_and_exposure() -> None:
    portfolio = initial_portfolio(Decimal("10000"))
    portfolio = apply_fill(
        portfolio, fill("fill-1", "AAPL", PortfolioSide.BUY, 10, "100", "10")
    ).portfolio
    portfolio = apply_fill(
        portfolio, fill("fill-2", "MSFT", PortfolioSide.BUY, 20, "50", "5")
    ).portfolio

    valuation = mark_to_market(
        portfolio,
        {"aapl": Decimal("120"), "MSFT": Decimal("40")},
        timestamp=timestamp(1),
    )

    assert portfolio.cash == Decimal("7985")
    assert valuation.equity == Decimal("9985")
    assert valuation.realized_pnl == Decimal("0")
    assert valuation.unrealized_pnl == Decimal("-15")
    assert valuation.gross_exposure_pct == Decimal("2000") / Decimal("9985")
    assert valuation.position_for("AAPL").unrealized_pnl == Decimal("190")  # type: ignore[union-attr]
    assert valuation.position_for("MSFT").unrealized_pnl == Decimal("-205")  # type: ignore[union-attr]


def test_portfolio_allocates_entry_commission_across_partial_and_final_sales() -> None:
    portfolio = initial_portfolio(Decimal("2000"))
    portfolio = apply_fill(
        portfolio, fill("fill-1", "AAPL", PortfolioSide.BUY, 10, "100", "10")
    ).portfolio

    partial_sale = apply_fill(portfolio, fill("fill-2", "AAPL", PortfolioSide.SELL, 4, "120", "4"))
    position = partial_sale.portfolio.position_for("AAPL")
    valuation = mark_to_market(
        partial_sale.portfolio, {"AAPL": Decimal("120")}, timestamp=timestamp(1)
    )
    final_sale = apply_fill(
        partial_sale.portfolio, fill("fill-3", "AAPL", PortfolioSide.SELL, 6, "120", "6")
    )

    assert partial_sale.realized_pnl == Decimal("72")
    assert position is not None
    assert position.quantity == 6
    assert position.entry_commission == Decimal("6")
    assert valuation.unrealized_pnl == Decimal("114")
    assert final_sale.realized_pnl == Decimal("108")
    assert final_sale.portfolio.positions == ()
    assert final_sale.portfolio.realized_pnl == Decimal("180")
    assert final_sale.portfolio.cash == Decimal("2180")


def test_portfolio_rejects_invalid_long_only_accounting_and_incomplete_marks() -> None:
    portfolio = initial_portfolio(Decimal("100"))

    with pytest.raises(PortfolioAccountingError, match="insufficient cash"):
        apply_fill(portfolio, fill("fill-1", "AAPL", PortfolioSide.BUY, 2, "100"))
    with pytest.raises(PortfolioAccountingError, match="without an open"):
        apply_fill(portfolio, fill("fill-2", "AAPL", PortfolioSide.SELL, 1, "100"))

    portfolio = apply_fill(portfolio, fill("fill-3", "AAPL", PortfolioSide.BUY, 1, "100")).portfolio
    with pytest.raises(ValueError, match="missing market prices"):
        mark_to_market(portfolio, {}, timestamp=timestamp())


def test_fixed_percentage_sizing_uses_marked_equity_and_available_cash() -> None:
    portfolio = initial_portfolio(Decimal("1000"))
    portfolio = apply_fill(portfolio, fill("fill-1", "AAPL", PortfolioSide.BUY, 5, "100")).portfolio
    valuation = mark_to_market(portfolio, {"AAPL": Decimal("100")}, timestamp=timestamp(1))

    aapl_size = FixedPercentageSizer(Decimal("0.6")).size(
        portfolio, valuation, symbol="AAPL", reference_price=Decimal("100")
    )
    msft_size = FixedPercentageSizer(Decimal("0.9")).size(
        portfolio, valuation, symbol="MSFT", reference_price=Decimal("200")
    )

    assert aapl_size.target_notional == Decimal("600.0")
    assert aapl_size.current_notional == Decimal("500")
    assert aapl_size.quantity == 1
    assert aapl_size.limited_by_cash is False
    assert msft_size.quantity == 2
    assert msft_size.limited_by_cash is True
