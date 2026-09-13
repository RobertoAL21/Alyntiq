# Backtesting Engine

## Scope

Phase 7 provides a deterministic, in-memory historical simulator. It is intentionally
independent from FastAPI, PostgreSQL, brokers, model inference, risk rules, and concrete
strategy implementations.

The `app.backtesting` package defines these explicit interfaces and value objects:

- `Strategy`: protocol that observes a completed bar and returns zero or one `Signal`.
- `Signal`, `Order`, and `Fill`: the strategy proposal, pending execution, and simulated
  execution record.
- `Position`, `Portfolio`, and `Trade`: long-only accounting state and closed quantities.
- `EquityPoint`, `BacktestMetrics`, and `BacktestResult`: historical output and evaluation.

## Execution Timeline

```text
bar at t closes → strategy observes bar at t → signal/order at t
next bar at t+1 opens → pending order fills at adjusted open
bar at t+1 closes → portfolio is marked to close → next strategy decision
```

Fills use the next available bar's opening price. Buy fills add slippage and sell fills
subtract it. Commission is a configurable percentage of fill notional. This timing avoids
using a closing price to decide and execute on that same close.

The final-bar order is cancelled because no later opening price exists. Orders that would
make cash negative or sell more than the open long position are rejected. These are
accounting invariants, not Phase 10 risk decisions.

## Deliberate Phase 7 Limits

The engine supports one symbol and long-only positions. It does not persist simulations,
choose a strategy, size positions through risk rules, submit broker orders, or support
shorting, leverage, multiple assets, or live/paper trading. Those capabilities belong to
later phases.

## Costs and Metrics

`BacktestConfig` defaults to the phase-required virtual initial cash of `100000 USD` and
requires research cost assumptions to be explicit through `commission_rate` and
`slippage_bps`. Their defaults are zero; they must not be interpreted as market estimates.

Metrics use the equity curve and closed-trade net PnL. Daily returns use the configured
trading-days-per-year value (default `252`) and a zero risk-free rate. The engine reports:

- total return, annualized arithmetic return, and CAGR;
- volatility, Sharpe ratio, Sortino ratio, and maximum drawdown;
- win rate, profit factor, trade count, and average/best/worst closed trade.

Metrics that are mathematically undefined for the available history, such as a Sharpe
ratio with zero volatility, are returned as `null` rather than invented.

## Manual Verification

The automated tests demonstrate a buy signal created at one close, execution at the next
open with slippage and commission, a later sell, a completed trade, and a rejected
insufficient-cash order. Run them from `backend/`:

```bash
ruff format --check .
ruff check .
pytest tests/test_backtest_engine.py tests/test_backtest_metrics.py
```

Backtest outputs are historical research results only. They do not imply future returns
and are not financial advice.
