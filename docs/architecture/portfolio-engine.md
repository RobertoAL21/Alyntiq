# Portfolio Engine

## Scope

Phase 11 introduces the pure `app.portfolio` package for multi-asset, long-only portfolio
accounting. It receives executed `PortfolioFill` values and explicit completed market
prices; it does not submit orders, fetch prices, connect to a broker, or run paper
trading.

```text
executed fill -> portfolio ledger -> completed prices -> portfolio valuation
                                         |
                                         -> fixed-percentage size proposal
```

The immutable `Portfolio` ledger contains initial cash, current cash, sorted open
positions, and cumulative realized PnL. Each position retains its average entry price and
unallocated entry commission.

## Accounting and valuation

Buying adds or increases an independent symbol position and deducts notional plus
commission from cash. Selling reduces only that symbol's existing long position. Entry
commission is allocated pro rata across partial sales, ensuring that realized and
unrealized PnL account for every commission exactly once.

`mark_to_market` requires a positive completed price for every open symbol and produces a
`PortfolioValuation` with:

- cash and equity;
- cumulative realized PnL and current unrealized PnL;
- a valuation for every open position; and
- per-position and gross long exposure as a percentage of equity.

It intentionally rejects incomplete market-price maps rather than inventing values.

## Fixed-percentage sizing

`FixedPercentageSizer` calculates an incremental whole-share buy quantity for a configured
target fraction of marked equity. It compares that target with the symbol's current marked
notional and caps the result by available cash. Its output is only a `PositionSize` value;
strategy, risk, and execution layers remain responsible for whether and how to use it.

This first sizing policy is not volatility-adjusted and does not apply Kelly sizing. It
also does not estimate commission, slippage, leverage, shorting, or partial fills. The
ledger itself remains independent from the Phase 12 paper-broker adapter.

## Relationship to historical backtesting

The Phase 7 backtest keeps its intentionally isolated one-symbol accounting model. This
multi-asset ledger is not retrofitted into it during Phase 11, because multi-asset strategy
scheduling and order execution are separate concerns. Both use explicit, immutable values
and long-only cash constraints, but neither is a broker integration.

## Verification

From `backend/`, run:

```bash
ruff format --check .
ruff check .
pytest tests/test_portfolio_engine.py
```
