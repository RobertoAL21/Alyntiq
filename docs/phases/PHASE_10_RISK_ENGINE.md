Phase 10 — Risk Engine

Status: COMPLETE

Architecture

Strategy
→ Proposed Trade
→ Risk Engine
→ Approved / Rejected
→ Execution

Rules

* maximum_position_size_pct
* maximum_portfolio_exposure
* maximum_daily_loss
* maximum_drawdown
* stop_loss
* take_profit
* max_trades_per_day
* minimum_cash_reserve

RiskDecision

Fields:

* approved
* reason
* rule
* original_order
* modified_order
