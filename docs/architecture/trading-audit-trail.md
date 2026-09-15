# Trading Audit Trail

## Scope

Phase 14 adds the `app.audit` package and persistent `trading_decisions` records. A decision
captures the full trace available at the time it is made:

```text
strategy lineage + prediction + signal + risk decision
    -> TradingDecision -> broker order id -> execution price and quantity
```

The record contains the required decision id, timestamp, symbol, model/strategy/feature
versions, prediction, confidence, signal, risk decision, order id, execution state, price,
quantity, and reason.

## Lifecycle and immutability

`TradingAuditService.record_risk_decision` creates a record from an explicit
`RiskDecision`, retaining original strategy lineage and the resulting proposed quantity.
Callers supply prediction and confidence because the audit layer must not infer model output.

An approved decision can subsequently receive one broker order id, then one execution price
and quantity. Repeating the exact same order or execution report is idempotent. A different
order id, price, or quantity is rejected rather than overwriting history. Rejected and
not-evaluated decisions cannot be linked to an order or execution.

The database enforces valid signal/risk values, positive price/quantity, execution details,
one record per decision UUID, and one decision per broker order id. An index on
`symbol, timestamp` supports reconstruction by instrument and time.

## Boundaries

The audit package records supplied facts; it does not calculate predictions, approve risk,
submit an order, poll a broker, or mark a portfolio. Phase 12 has no automated execution
workflow, so callers must deliberately invoke audit methods around any future broker call.
This phase adds no API route, background worker, or frontend.

## Verification

Apply the migration, then run from `backend/`:

```bash
alembic upgrade head
ruff format --check .
ruff check .
pytest tests/test_trading_audit.py
```
