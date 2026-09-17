# Hybrid Strategy

## Scope

Phase 19 defines a pure strategy-side composition of existing research inputs. It accepts
already prepared point-in-time inputs and produces at most one long-only proposal after a
completed backtest bar. It does not calculate features, fit models, fit regimes, analyze
articles, choose thresholds, evaluate risk, size a position, or execute an order.

```text
ML prediction + quantitative context + regime classification + prior news signals
                                      |
                                      v
                              HybridStrategy proposal
                                      |
                                      v
                       existing risk and next-open backtest execution
```

## Inputs and timing

`HybridStrategyInputs` indexes predictions, quantitative context, and regime
classifications by exactly their point-in-time timestamp. The index keys must equal their
value timestamps. A missing input means HOLD; a prediction or quantitative-symbol mismatch
is rejected rather than being applied to another asset.

News signals are only considered for the current bar symbol when their publication time is
at or before the completed bar, inside an explicit lookback window (three days by default).
Future news is ignored. No labels or outcomes are available to the strategy.

## Proposal rules

The initial, documented research rule proposes BUY only when all conditions hold:

- the validation-selected ML threshold classifies the prediction as BUY;
- quantitative trend and momentum are both positive;
- the regime is `bull` with low volatility; and
- accumulated relevant news sentiment is non-negative.

For an open long position, it proposes SELL if the ML threshold is SELL, both quantitative
measures are negative, the regime is bear or high volatility, or the news score is below
the configured negative threshold. Otherwise it holds. These are transparent baseline
rules, not optimized parameters or claims of profitability.

Every hybrid proposal preserves existing ML model, feature, and strategy lineage in
`SignalLineage`. Risk and execution retain their independent existing boundaries.

## Comparison

`build_hybrid_competitors` supplies fresh strategy factories to the Phase 16
`StrategyCompetitionService` for five like-for-like competitors:

- Buy & Hold;
- Momentum;
- pure ML threshold strategy;
- news-only sentiment strategy; and
- the hybrid strategy.

They share bars and `BacktestConfig`, while each gets an independent virtual portfolio.

## Verification

From `backend/`, run:

```bash
ruff format --check .
ruff check .
pytest tests/test_hybrid_strategy.py
```
