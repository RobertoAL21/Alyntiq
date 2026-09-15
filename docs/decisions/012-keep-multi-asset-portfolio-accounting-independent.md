# ADR 012: Keep multi-asset portfolio accounting independent

## Status

Accepted

## Context

The existing historical backtest has a deliberately simple one-symbol portfolio model.
Phase 11 requires cash, positions, equity, PnL, and exposure across multiple assets, but
does not include multi-asset order scheduling, broker execution, or paper trading.

Extending the Phase 7 simulator directly would conflate simulation timing with portfolio
accounting and make the future execution boundary unclear.

## Decision

Create a pure `app.portfolio` ledger that accepts already-executed multi-asset fills and
explicit market prices. The ledger is immutable, long-only, and cash-constrained. It
calculates realized PnL while applying fills and unrealized PnL/exposure only when marked
with a complete price map.

Add a fixed-percentage sizer that produces an incremental whole-share quantity from marked
equity and available cash. It returns a value object only; it does not create an order or
bypass strategy, risk, or execution decisions.

## Consequences

- Multi-asset accounting can be tested independently from historical backtesting and a
  future paper broker.
- Commissions are allocated consistently between partial realized PnL and remaining
  unrealized PnL.
- The initial implementation excludes shorting, leverage, volatility sizing, Kelly sizing,
  fees in sizing, and execution semantics.
- A future execution layer can convert broker fills into this ledger without making the
  portfolio package depend on a broker SDK.
