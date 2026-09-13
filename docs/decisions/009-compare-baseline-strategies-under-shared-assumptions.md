# ADR 009 — Compare Baseline Strategies Under Shared Historical Assumptions

## Status

Accepted

## Context

Phase 8 introduces strategies that make different trading decisions. Comparing their
returns across different symbols, time ranges, execution costs, quantities, or random
seeds would confound strategy behavior with different experimental conditions.

The Phase 7 engine is single-symbol and long-only. Position-sizing and risk policies are
not yet available and must not be silently embedded in an individual baseline strategy.

## Options Considered

### Let each strategy choose its own data period and cost settings

This is flexible, but the resulting metrics cannot support a fair comparison.

### Hardcode allocation and cost assumptions inside strategies

This hides financial assumptions in strategy code and prematurely combines strategy with
position sizing and execution policy.

### Run fresh strategies through one shared comparison service

This keeps decision logic separate and makes the full experimental context explicit.

## Decision

The baseline comparison service loads a single source-qualified daily-bar series and runs
fresh Buy & Hold, Moving Average Crossover, RSI Mean Reversion, Momentum, and Random
strategy instances with one shared `BacktestConfig` and fixed whole-share quantity.

The random strategy uses an explicit seed. Costs, quantity, date range, and indicator
parameters are inputs to the run rather than hidden choices. The leaderboard ranks total
return but includes risk-adjusted and trade-count metrics for context.

## Consequences

Phase 8 produces reproducible, like-for-like historical baseline comparisons. It does not
select parameters using a test period, implement risk-based sizing, create model-driven
signals, or connect to a broker. Those decisions remain in later phases.
