# Model Registry

## Scope

Phase 21 adds a persistent lifecycle record for a reproducible model version. It does not
train, tune, serve, deploy, monitor, or automatically select a model. A registered model
is evidence and lifecycle metadata; it is not an inference implementation.

```text
experiment / backtest evidence
             |
             v
candidate -> staging -> production -> retired
                              |
                              v
                 model-driven paper-order eligibility
```

## Registry record

Every version is globally unique and begins as `candidate`. Its immutable registration
contains the model name and family; dataset, feature, and target versions; JSON-compatible
parameters, predictive metrics, and backtest results; and an artifact URI. The mutable
fields are only the lifecycle state and its update time.

This keeps the registry independent of MLflow: MLflow remains the experiment tracker,
while the registry records the reviewed artifact and evidence that a paper-trading flow is
allowed to reference.

## Lifecycle

Allowed transitions are deliberate:

- `candidate` to `staging` or `retired`;
- `staging` to `candidate`, `production`, or `retired`;
- `production` to `staging` or `retired`; and
- `retired` is terminal.

There is no direct candidate-to-production transition. Registering the same version with
identical provenance is idempotent; changing its evidence requires a new model version.

## Paper-trading gate

`submit_approved_order` still requires an approved independent `RiskDecision`. If that
decision carries model lineage, the caller must additionally provide a database session
and the registry gate. The gate rejects every state except `production` before the broker
receives an order. Orders without model lineage retain the existing non-model execution
path.

The registry does not change strategy logic, risk rules, broker endpoints, or live-trading
safety. No route, worker, model serving, deployment, or monitoring integration is added.

## CLI

From `backend/`, register a reviewed candidate with explicit evidence:

```bash
python -m scripts.register_model \
  --model-name transformer \
  --model-version transformer-v1 \
  --model-family deep_learning \
  --dataset-version dataset-v1 \
  --feature-version features-v1 \
  --target-version targets-v1 \
  --parameters '{"lookback": 20}' \
  --metrics '{"holdout_roc_auc": 0.61}' \
  --backtest-results '{"sharpe_ratio": 0.8}' \
  --artifact-uri file:///mlruns/artifacts/transformer-v1
```

Promote it only through valid lifecycle states:

```bash
python -m scripts.set_model_state --model-version transformer-v1 --state staging
python -m scripts.set_model_state --model-version transformer-v1 --state production
```
