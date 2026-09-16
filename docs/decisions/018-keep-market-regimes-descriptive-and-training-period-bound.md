# ADR 018: Keep market regimes descriptive and training-period bound

## Status

Accepted

## Context

Market-regime labels are unsupervised research outputs. Fitting a scaler or clustering
model with observations from a later evaluation period would leak future distributional
information into an earlier label. Treating a cluster label as a strategy, risk approval,
or execution instruction would also violate the system's domain boundaries.

## Decision

Create a pure regime package with trailing SPY/QQQ feature calculation and an explicit
`fit` then `classify` interface. The detector learns scaling, cluster-to-description
mapping, and the high-volatility threshold only from the supplied chronological training
features. KMeans, Gaussian Mixture, and scikit-learn HDBSCAN are available as research
methods.

Use bull, bear, and sideways names only as an ordering of training-period cluster trend;
report volatility separately as high or low. HDBSCAN noise remains unclassified. Later
observations are assigned to the nearest prior HDBSCAN cluster center, without refitting
or claiming a probabilistic forecast.

## Consequences

* Regime experiments can be reproduced with their feature, model, and training-period
  configuration.
* Regime results remain a possible later strategy context, never a trade decision.
* Persisting classifications, connecting them to a strategy, and validating their impact
  on returns remain future work.
