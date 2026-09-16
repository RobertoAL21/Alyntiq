Phase 17 — Market Regime Detection

Status: COMPLETE

Features

* volatility
* returns
* trend
* volume
* correlations

Models

* KMeans
* Gaussian Mixture Models
* HDBSCAN

Potential Labels

* bull
* bear
* sideways
* high volatility
* low volatility

Use regime information as research input and later strategy context.

Delivered:

* trailing SPY/QQQ features for return, trend, annualized volatility, relative volume,
  and rolling return correlation;
* reproducible KMeans, Gaussian Mixture, and HDBSCAN regime detectors using an explicit
  chronological training period; and
* descriptive bull, bear, sideways, high-volatility, and low-volatility classifications.

The detector is research infrastructure only. It does not train trading models, emit
strategy proposals, choose risk limits, or submit orders.
