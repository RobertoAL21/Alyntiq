# Risk Engine

## Scope

Phase 10 introduces `app.risk`, an independent pre-trade evaluator. It separates a
strategy's proposed order from the decision to allow, reduce, or reject that order:

```text
Strategy signal -> ProposedOrder -> RiskEngine -> RiskDecision -> backtest pending order
```

`RiskDecision` always retains the original order and exposes `approved`, `reason`,
`rule`, and an optional modified order. This makes a strategy proposal distinguishable
from the order that the simulator may execute.

## Risk limits

`RiskLimits` makes every limit explicit. A `None` value disables that limit; there are no
implicit sizing or loss assumptions. The supported limits are:

- maximum position size as a percentage of marked equity;
- maximum single-symbol portfolio exposure;
- maximum daily realized loss as a percentage of marked equity;
- maximum drawdown from the observed equity-curve peak;
- maximum completed orders per day;
- minimum cash reserve; and
- stop-loss and take-profit percentages relative to the average long entry price.

For a buy proposal, the engine applies all enabled notional and cash caps in sequence.
It returns a reduced quantity when a positive quantity remains, otherwise it rejects the
proposal with the rule that prevented it. Sell proposals reduce an existing long position
and are allowed by the pre-trade limits.

## Historical integration

The backtest engine constructs the risk context only after a bar has closed. It asks the
risk engine to evaluate a strategy proposal before it becomes a pending order. An approved
order still fills only at the next bar open under the Phase 7 execution policy.

Stop-loss and take-profit checks also use the completed bar close. A triggered protection
creates a full long-position sell proposal that is likewise filled at the next open. This
preserves the no-look-ahead timeline; it is not an intrabar stop execution model.

The risk engine does not mutate portfolio state, place broker orders, train models, or
implement paper/live trading.

## Verification

From `backend/`, run:

```bash
ruff format --check .
ruff check .
pytest tests/test_risk_engine.py
```
