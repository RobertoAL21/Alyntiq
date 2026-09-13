# Baseline Strategies

## Scope

Phase 8 implements five deterministic, long-only strategy implementations in
`app.strategies.baselines`:

- `buy_and_hold`: sends one buy signal after the first observed bar and holds.
- `moving_average_crossover`: buys on a fast/slow moving-average cross above and sells
  when it crosses below.
- `rsi_mean_reversion`: buys below the oversold RSI threshold and sells above the
  overbought threshold.
- `momentum`: buys when the close is above its configured lookback close and sells when
  it is not.
- `random`: randomly alternates between buy and sell opportunities using a fixed seed.

Strategies only observe the current completed bar, their own trailing close history, and
the immutable portfolio supplied by the backtesting engine. They do not calculate fills,
commissions, slippage, risk approvals, or broker requests.

## Fair Comparison Contract

`BaselineStrategyComparisonService` loads one provenance-qualified symbol series once,
then creates a new `BacktestEngine` for each fresh strategy instance. Every strategy
receives the same:

- symbol, source, daily-bar timeframe, inclusive start date, and inclusive end date;
- initial cash, commission rate, slippage assumption, and trading-days-per-year setting;
- fixed whole-share quantity;
- strategy parameter values, with a fixed random seed for the random baseline.

The service returns the individual `BacktestResult` values and a leaderboard ordered by
total return. The leaderboard also exposes Sharpe ratio, Sortino ratio, maximum drawdown,
and the number of closed trades so return is not interpreted alone.

## Signal Timing and Indicators

Every signal is generated only after appending the current bar's close to that strategy's
trailing history. The Phase 7 engine executes it at the next bar open, as defined in
[ADR 008](../decisions/008-next-bar-open-backtest-execution.md). No indicator reads a
later bar.

The initial, explicit indicator parameters are research baselines rather than optimized
claims: fast/slow moving averages of 20/50 bars, RSI window 14 with 30/70 thresholds,
and 20-bar momentum. The CLI exposes them for a documented research run, but selecting
parameters based on a final test period is outside this phase.

## CLI

From the repository root, compare all five strategies over the same stored data period:

```bash
docker compose exec backend python -m scripts.run_baseline_strategies \
  --symbol AAPL \
  --start 2024-01-02 \
  --end 2024-12-31 \
  --quantity 100 \
  --commission-rate 0.001 \
  --slippage-bps 5
```

`--quantity` is intentionally required: position sizing and risk limits are not yet
implemented. The command emits JSON with the data provenance, shared cost assumptions,
and comparison metrics. Its results are historical research results, not financial advice
or a paper-trading instruction.
