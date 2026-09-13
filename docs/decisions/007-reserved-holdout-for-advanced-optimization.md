# ADR 007 — Reserve the Final Walk-Forward Fold for Advanced-Model Evaluation

## Status

Accepted

## Context

Advanced tree models have more hyperparameters than Phase 5 baselines. Using the final
evaluation period to choose their settings would tune against the very result used for
comparison and overstate expected predictive performance.

## Options Considered

### Optimize on all walk-forward folds

This uses more observations for hyperparameter selection, but leaves no untouched
period for final comparison.

### Use one fixed validation split and one final holdout

This is simple, but uses less historical validation evidence when selecting parameters.

### Optimize on earlier expanding folds and reserve the final fold

This preserves repeated chronological validation for Optuna while retaining a later,
unseen period for a single final evaluation.

## Decision

Phase 6 uses the earlier expanding walk-forward folds for seeded Optuna TPE searches.
The final fold is reserved from optimization and evaluated once after each model family
is fitted with its selected parameters. The existing one-timestamp target gap remains
mandatory.

Random Forest, XGBoost, and LightGBM provide native feature importances. Those values
and a holdout-only leaderboard are tracked in MLflow. SHAP is optional and deferred to
avoid adding another dependency before an explanation use case is defined.

## Consequences

The final holdout score is a more credible model-comparison metric, but optimization
uses fewer folds and has higher variance than tuning on all available data.

The leaderboard ranks predictive metrics only. It cannot be used to choose a trading
strategy until backtesting and risk phases exist.
