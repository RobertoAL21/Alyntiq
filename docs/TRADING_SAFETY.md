Alyntiq — Trading Safety Rules

Scope

Alyntiq currently supports:

* research
* backtesting
* paper trading

Default Environment

TRADING_ENVIRONMENT must default to:

paper

Live Trading

Real-money execution must not be enabled accidentally.

If live trading is ever introduced, it must require an explicit future architecture decision and additional safeguards.

Broker Credentials

Never commit:

* API keys
* secret keys
* tokens

Use environment variables.

Risk Separation

Trading strategies must not bypass the risk engine.

Flow:

Strategy
→ Proposed Order
→ Risk Engine
→ Approved Order
→ Execution

Risk Rules

The system will eventually support:

* maximum position size
* maximum portfolio exposure
* maximum daily loss
* maximum drawdown
* maximum trades per day
* stop loss
* take profit
* minimum cash reserve

No Guaranteed Returns

Documentation and UI must not suggest guaranteed performance.

Use terms such as:

* historical performance
* experimental result
* backtest result
* paper trading result