# Deep-Learning Time-Series Research

## Scope

Phase 20 evaluates four fixed PyTorch binary classifiers: LSTM, GRU, temporal CNN, and
a small Transformer encoder. They consume versioned market features and predict the
existing next-day direction target. This is predictive research only: it does not create
a strategy, select a trading threshold, backtest, approve risk, execute an order, or
register a model for paper trading.

## Sequence construction and timing

The training-dataset repository retains the symbol alongside each already aligned feature
and target row. `build_temporal_sequences` sorts each symbol independently and creates a
trailing window ending at timestamp `t`:

```text
x(t-lookback+1) ... x(t) -> direction_1d(t)
```

The target continues to mean the close movement from `t` to `t + 1`; a window never
contains a later feature row and never crosses symbols. Features are scaled by a
`StandardScaler` fitted only to the training sequences of each fold.

## Evaluation boundary

The existing timestamp-aligned expanding walk-forward splitter is applied after window
construction. It retains the mandatory one-timestamp gap required by the next-day target.
Earlier folds are validation evidence, while the final chronological fold is untouched
until one evaluation per architecture.

```text
per-symbol feature windows -> expanding validation folds -> architecture comparison
                                                    \
                                                     -> final untouched holdout
```

The same folds and holdout also evaluate the existing random, majority-class, logistic
regression, and decision-tree baselines from the most recent feature row in each window.
The shared holdout leaderboard ranks all eight controls and models by ROC-AUC, then
accuracy. It compares predictive quality only; it cannot establish trading performance or
select a paper-trading model.

## Reproducibility and tracking

All models use CPU PyTorch, a configured seed, deterministic algorithms where supported,
fixed network settings, and fixed training epochs. MLflow records dataset/feature/target
lineage, sequence and network settings, validation metrics, mean validation metrics,
holdout metrics, individual result artifacts, and the holdout leaderboard.

## CLI

From `backend/`, after generating matching feature and target versions:

```bash
python -m scripts.run_deep_learning_models \
  --source alpaca:iex:raw \
  --timeframe 1D \
  --feature-version features-v1 \
  --target-version targets-v1 \
  --dataset-version dataset-v1 \
  --n-splits 3 \
  --gap 1 \
  --lookback 20 \
  --epochs 10
```

The command is deliberately an offline research entry point. Model lifecycle, serving,
drift monitoring, observability, and CI/CD remain outside Phase 20.
