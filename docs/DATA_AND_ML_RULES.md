Alyntiq — Data and Machine Learning Rules

Most Important Rule

Never introduce future information into features.

This includes direct and indirect leakage.

Time-Series Validation

Do not use random train/test splits for market time-series experiments.

Prefer:

* chronological splits
* expanding windows
* rolling windows
* walk-forward validation

Example:

Train:
2020-2022

Validation:
2023

Test:
2024

Then move forward.

Dataset Versioning

Experiments should record:

* dataset version
* feature version
* target version
* model version

Feature Rules

Features calculated at timestamp t may only use information available at or before t.

Examples:

Valid:

rolling mean using t and previous observations.

Invalid:

feature using close(t+1).

Target Isolation

Targets must remain separate from inference features.

Do not include targets in model input.

Model Evaluation

Track predictive metrics such as:

* accuracy
* precision
* recall
* F1
* ROC-AUC

But do not use predictive metrics as the sole trading evaluation.

Trading Evaluation

Strategies should also be measured by:

* total return
* CAGR
* volatility
* Sharpe ratio
* Sortino ratio
* maximum drawdown
* win rate
* profit factor
* number of trades

Baselines

Every advanced model must be compared against simple alternatives.

Hyperparameter Optimization

Optimization must use training and validation data only.

The test set must never be used to tune parameters or thresholds.

Reproducibility

When practical, record:

* random seed
* dependencies
* training date
* source data range
* feature version
* target version
* parameters