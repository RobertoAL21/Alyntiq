# Strategy Competition

## Scope

Phase 16 provides a pure historical-research service for comparing supplied strategies
under identical market data and explicit backtest assumptions. It does not train or infer
models, select thresholds, apply risk policy, submit broker orders, persist a result, or
run paper trading.

```text
shared completed bars + shared BacktestConfig + named strategy factories
                              |
                              v
          one fresh strategy + one BacktestEngine + one virtual portfolio per competitor
                              |
                              v
             complete per-strategy results + comparable performance leaderboard
```

`StrategyCompetitionService` accepts `StrategyCompetitor` values, each with a distinct
name and a factory that creates fresh strategy state. Every factory is run once against
the same ordered, single-symbol `BacktestBar` collection with the same `BacktestConfig`.
Because each `BacktestEngine` initializes its own Phase 7 portfolio, cash, position,
orders, fills, trades, and equity curve cannot leak between competitors.

## Metrics and ordering

The service returns every `VirtualPortfolioRun` as well as a deterministic leaderboard.
It ranks total return descending, with strategy name ascending as the tie-breaker, and
retains Sharpe ratio, Sortino ratio, maximum drawdown, and closed-trade count. Results are
historical research metrics, not a claim of expected profitability or financial advice.

## Relationship to other domains

The competition preserves the Phase 7 next-bar-open timing, commission, and slippage
assumptions. It deliberately reuses the isolated one-symbol backtesting portfolio rather
than the Phase 11 multi-asset ledger, whose purpose is accounting already-executed fills.

Buy & Hold, Momentum, and Mean Reversion can be supplied as baseline factories. An ML
competitor must remain an `MLThresholdStrategy` supplied with point-in-time predictions
and validation-selected thresholds. Hybrid strategies are not included before Phase 19.

## Verification

From `backend/`, run:

```bash
ruff format --check .
ruff check .
pytest tests/test_strategy_competition.py tests/test_baseline_strategy_comparison.py
```
