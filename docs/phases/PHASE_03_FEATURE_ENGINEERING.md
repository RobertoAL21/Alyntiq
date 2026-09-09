Phase 3 — Feature Engineering

Objective

Create reproducible ML features.

Features

Returns

* returns_1d
* returns_5d
* returns_10d
* returns_20d

Momentum

* momentum_5
* momentum_10
* momentum_20

Moving Averages

* sma_10
* sma_20
* sma_50
* ema_10
* ema_20

Volatility

* volatility_10
* volatility_20
* atr_14

Technical

* rsi_14
* macd
* macd_signal
* bollinger_upper
* bollinger_lower

Volume

* volume_change
* volume_ma_20
* volume_ratio

Market Context

* SPY return
* QQQ return
* SPY volatility

Versioning

Introduce:

feature_version

Example:

features-v1

Critical Rule

No future information.

Add leakage tests.