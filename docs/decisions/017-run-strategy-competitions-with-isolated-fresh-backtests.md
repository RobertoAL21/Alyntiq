# ADR 017: Run strategy competitions with isolated fresh backtests

## Status

Accepted

## Context

Phase 16 needs comparable historical results for multiple strategies. Reusing a strategy
instance or portfolio between competitors would carry trailing indicators, positions,
cash, or realized PnL from one result into another. Retrofitting the Phase 11 multi-asset
ledger into the Phase 7 simulator would also conflate executed-fill accounting with
historical order timing.

## Decision

Use a pure `StrategyCompetitionService` that accepts named strategy factories, one shared
ordered bar collection, and one explicit `BacktestConfig`. It creates a new strategy and
a new Phase 7 `BacktestEngine` for every competitor. Each engine therefore owns its own
virtual long-only portfolio while retaining the existing next-open execution, commission,
and slippage behavior.

The leaderboard ranks total return and includes Sharpe, Sortino, maximum drawdown, and
closed-trade count. Baseline comparison delegates to this service.

## Consequences

* Competitions are reproducible when their strategy factories and backtest inputs are
  reproducible.
* The service can compare baseline and already-configured ML strategy factories without
  taking ownership of model inference or threshold selection.
* Hybrid strategies, multi-asset scheduling, risk-policy selection, persistence, and
  broker execution remain outside this phase.
