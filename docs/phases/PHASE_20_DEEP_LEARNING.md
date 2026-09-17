Phase 20 — Advanced Time-Series Models

Status: COMPLETE

Research:

* LSTM
* GRU
* Temporal CNN
* Temporal Fusion Transformer
* time-series Transformers

Technology:

PyTorch.

Delivered:

* symbol-local trailing windows over versioned features, ending at the existing next-day
  direction target timestamp;
* reproducible CPU LSTM, GRU, temporal CNN, and Transformer classifier experiments;
* timestamp-aligned expanding validation folds, a one-timestamp target gap, and one
  untouched final holdout per architecture;
* a like-for-like holdout comparison with the existing random, majority-class, logistic
  regression, and decision-tree baselines; and
* MLflow lineage, parameters, validation and holdout metrics, result artifacts, and a
  predictive holdout leaderboard.

Rule

Deep learning must prove its value against simpler baselines.

Do not assume higher complexity means better performance.

The comparison remains offline predictive research. It does not create a trading strategy,
model registry entry, monitoring integration, deployment, or CI/CD workflow.
