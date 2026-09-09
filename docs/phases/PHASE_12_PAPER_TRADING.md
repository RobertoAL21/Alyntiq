Phase 12 — Paper Trading

Provider

Alpaca Paper Trading.

Safety

Require:

TRADING_ENVIRONMENT=paper

Block execution otherwise.

Interface

BrokerInterface

Methods:

* submit_order
* cancel_order
* get_positions
* get_account
* get_orders

Implementation:

AlpacaPaperBroker

Backtesting and paper trading should share the same strategy logic.