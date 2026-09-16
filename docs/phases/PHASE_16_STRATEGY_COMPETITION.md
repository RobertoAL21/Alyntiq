Phase 16 — Strategy Competition

Status: COMPLETE

Give each strategy identical starting capital.

Example:

$20,000 each.

Competitors may include:

* Buy & Hold
* Momentum
* Mean Reversion
* XGBoost
* LightGBM
* Hybrid

Create independent virtual portfolios.

Delivered:

* a pure competition service that accepts named, fresh strategy factories;
* one independent Phase 7 virtual portfolio per competitor, each initialized with the
  identical explicit `BacktestConfig` and historical bars;
* a return-ranked leaderboard that retains Sharpe, Sortino, maximum-drawdown, and
  closed-trade-count context; and
* reuse of the same service by the existing baseline-strategy comparison.

Model-driven competitors can be supplied as `MLThresholdStrategy` factories with their
already point-in-time predictions and validation-selected thresholds. Hybrid strategies
remain out of scope until Phase 19.
