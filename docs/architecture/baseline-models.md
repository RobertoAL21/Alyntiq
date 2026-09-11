# Baseline Models

## Scope

Phase 5 evaluates simple classification baselines. It does not create a trading
strategy, a backtest, a risk decision, an order, or an inference API.

## Training Dataset

The training-data repository explicitly joins `market_features` and `market_targets`
only when their provenance-qualified bar identity matches. It selects one feature
version and one target version, excludes rows with warm-up feature nulls or unknown
targets, and returns the feature matrix (`X`) separately from the target vector (`y`).

```text
market_features (features-v1) ─┐
                               ├─ training dataset → X and y remain separate
market_targets (targets-v1)  ──┘
```

## Validation

Baseline evaluation uses expanding walk-forward windows aligned to unique timestamps.
Every test window is later than its training window. A one-timestamp gap separates
them because `direction_1d(t)` requires the next close; this prevents a training label
at the boundary from observing a close in the test period.

This deliberately avoids random train/test splits. The approach is consistent with
scikit-learn's time-series guidance that training observations must precede evaluation
observations. [TimeSeriesSplit documentation](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html)

## Models and Metrics

The fixed Phase 5 baselines are random prediction, majority class, logistic regression,
and decision tree. Each fold records accuracy, precision, recall, F1, and ROC-AUC.
ROC-AUC is stored as null when an evaluation fold has only one observed class.

## Experiment Tracking

Each baseline run is tracked in MLflow with its model and parameters, dataset, feature,
target, and model versions, source, timeframe, row count, per-fold metrics, average
metrics, and a `baseline_result.json` artifact. `MLFLOW_TRACKING_URI`,
`MLFLOW_ARTIFACT_URI`, and `MLFLOW_EXPERIMENT_NAME` are centralized settings. The local
tracking backend uses SQLite and Docker persists both its database and artifacts in the
`mlruns_data` volume.

## CLI

From `backend/`, after building matching features and targets:

```bash
python -m scripts.run_baselines \
  --source alpaca:iex:raw \
  --timeframe 1D \
  --feature-version features-v1 \
  --target-version targets-v1 \
  --dataset-version dataset-v1 \
  --n-splits 3 \
  --gap 1
```

The command prints aggregate metrics for research comparison. They are predictive
metrics only and do not represent trading performance or financial advice.
