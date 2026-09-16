# Market Regimes

## Scope

Phase 17 adds a pure `app.regimes` package for descriptive market-regime research. It
calculates only trailing inputs from completed SPY and QQQ bars, fits an unsupervised
model on an explicit earlier training period, then classifies separate later observations.

```text
completed SPY + QQQ bars
           |
           v
trailing return, trend, volatility, volume, correlation features
           |
           v
explicit chronological training period -> fitted regime detector -> later classifications
```

No API, storage, background worker, model inference, strategy proposal, risk decision,
broker order, or paper-trading action is introduced by this phase.

## Feature contract

`calculate_regime_features` uses a configurable trailing window (20 daily bars by
default) and returns a complete feature row only after all inputs are available:

- market return over the window;
- close relative to its trailing simple moving average as trend;
- annualized trailing daily-return volatility;
- volume relative to its trailing average; and
- trailing correlation between SPY and QQQ daily returns.

All windows include the current completed bar and never read a later bar. The calculator
rejects duplicate symbol/timestamp bars and missing configured market context.

## Detection contract

`MarketRegimeDetector.fit` accepts chronologically increasing `RegimeFeatures` from a
caller-selected training period. Its scaler, descriptive cluster mapping, and
high-volatility threshold are fitted solely on that period. `classify` uses that frozen
state for later features.

KMeans and Gaussian Mixture use a configured, seeded three-cluster baseline. Clusters are
ordered by their training-period mean trend: lowest is `bear`, highest is `bull`, and the
middle is `sideways`. Volatility is `high_volatility` at or above the training median and
`low_volatility` below it. These names are descriptive conventions, not predictions.

Scikit-learn's HDBSCAN is data-driven and can label training points as noise. Its detected
cluster centers are retained only to assign later research observations to the nearest
previously detected cluster; if HDBSCAN detected no cluster, the result is
`unclassified`. This is intentionally not presented as a probability or trade signal.

## Verification

From `backend/`, run:

```bash
ruff format --check .
ruff check .
pytest tests/test_market_regimes.py
```
