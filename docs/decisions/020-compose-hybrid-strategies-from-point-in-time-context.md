# ADR 020: Compose hybrid strategies from point-in-time context

## Status

Accepted

## Context

Phase 19 combines ML predictions, quantitative features, market regimes, and news
sentiment. Letting the strategy fetch, fit, or reinterpret those datasets would hide
timing assumptions, risk leakage from future data, and collapse the boundaries introduced
in earlier phases.

## Decision

Accept externally prepared, timestamp-indexed context values in a pure hybrid strategy.
Require all inputs for a BUY and treat missing input as HOLD. Use only news signals
published at or before the completed bar, within an explicit finite lookback. Reuse the
validation-selected ML thresholds and existing competition service.

Compare hybrid results with fresh Buy & Hold, Momentum, pure ML, and news-only strategy
factories under the same bars and `BacktestConfig`.

## Consequences

* Hybrid research is reproducible when its input collections, threshold-selection period,
  and backtest assumptions are retained.
* The implementation is a strategy, not a new model, regime detector, NLP system, risk
  policy, or execution component.
* Feature aggregation, parameter optimization, persistence, and live/paper integration
  remain outside this phase.
