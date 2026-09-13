# Advanced Models

## Scope

Phase 6 evaluates Random Forest, XGBoost, and LightGBM classifiers. It does not create
a trading strategy, a backtest, a risk decision, an order, an inference API, or a model
registry entry.

## Validation and Optimization Boundary

The existing expanding walk-forward splitter creates at least three folds. All folds
except the final one are used by Optuna to select hyperparameters by mean validation
ROC-AUC. The final fold is reserved and evaluated once after optimization; it is never
used by Optuna.

```text
earlier data → expanding train/validation folds → Optuna selection
later data   → reserved final fold              → one holdout evaluation
```

The mandatory one-timestamp gap remains in every fold because `direction_1d` uses the
next close. This keeps optimization separate from the holdout and prevents target
boundary contamination.

## Model Families

Each model uses a reproducible Optuna TPE sampler and a fixed random seed.

- Random Forest: `n_estimators`, `max_depth`, `min_samples_leaf`, `max_features`.
- XGBoost: `n_estimators`, `max_depth`, `learning_rate`, `subsample`,
  `colsample_bytree`, `min_child_weight`.
- LightGBM: `n_estimators`, `num_leaves`, `max_depth`, `learning_rate`, `subsample`,
  `colsample_bytree`, `min_child_samples`.

LightGBM's `num_leaves` is constrained to `2^max_depth`, consistent with its
[classifier documentation](https://lightgbm.readthedocs.io/en/latest/pythonapi/lightgbm.LGBMClassifier.html).
Optuna studies are seeded and limited to the requested number of trials using its
[study optimization API](https://optuna.readthedocs.io/en/stable/reference/generated/optuna.study.Study.html).

## Analysis and Tracking

The final model trained before the reserved holdout exposes native
`feature_importances_`; these values are stored as an MLflow artifact. SHAP is optional
in the phase definition and is intentionally not added as a dependency.

MLflow receives best hyperparameters, validation ROC-AUC, holdout metrics, Optuna trial
history, feature importance, a full result artifact, and the leaderboard. The leaderboard
ranks only Phase 6 models by untouched holdout ROC-AUC, then holdout accuracy.

## CLI

From `backend/`, after building matching features and targets:

```bash
python -m scripts.run_advanced_models \
  --source alpaca:iex:raw \
  --timeframe 1D \
  --feature-version features-v1 \
  --target-version targets-v1 \
  --dataset-version dataset-v1 \
  --n-splits 3 \
  --gap 1 \
  --n-trials 10
```

The printed leaderboard is a predictive-research comparison only. It is not trading
performance, a trading signal, or financial advice.
