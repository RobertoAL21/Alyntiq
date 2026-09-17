Phase 19 — Hybrid Strategy

Status: COMPLETE

Combine:

* quantitative features
* ML predictions
* market regime
* news sentiment

Compare against:

* pure ML
* momentum
* news-only
* Buy & Hold

Delivered:

* an input contract for versioned ML predictions, point-in-time quantitative context,
  descriptive market regimes, and structured news signals;
* a hybrid strategy that combines those inputs only into long-only BUY, SELL, or HOLD
  proposals; and
* common competition factories for Buy & Hold, Momentum, pure ML, news-only, and hybrid
  strategies under the same historical assumptions.

The hybrid strategy does not train models, select ML thresholds, approve risk, or execute
orders. It remains historical research infrastructure.
