Phase 14 — Trading Audit Trail

Create:

TradingDecision

Fields:

* id
* timestamp
* symbol
* model_version
* strategy_version
* feature_version
* prediction
* confidence
* signal
* risk_decision
* order_id
* executed
* price
* quantity
* reason

Goal:

Every trade must be reconstructable.