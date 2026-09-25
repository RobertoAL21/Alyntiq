# Paper Strategy Activation

## Scope

Phase 28 adds a persistent control-plane record for a future paper-trading worker. It is
not an execution loop and it does not invoke the model, strategy, risk engine, or broker.

```text
Dashboard/API -> deployment configuration -> validation -> armed configuration
                                                        |
                                                        +-> future worker (not implemented)
```

## Boundaries

The record pins a model version and its feature/target lineage, a strategy version, market
source/timeframe, symbols, thresholds, a proposed order quantity, and all `RiskLimits`.
The registry remains responsible for model lifecycle; the risk package remains responsible
for evaluating a future proposed order; the execution package remains the only broker
boundary.

Validation accepts only `TRADING_ENVIRONMENT=paper` and a registry model in `production`.
It compares feature and target versions to the registry and refuses deployments with any
unset risk limit. Repeating validation at arm time prevents a later model demotion or
configuration/environment change from bypassing the gate.

## Control access

Read-only deployment status is available through the dashboard API. Create, validate, arm,
and disarm endpoints require `X-Alyntiq-Control-Token`, compared to the configured
`DASHBOARD_CONTROL_TOKEN`. If the configured token is absent, mutations return an error and
remain disabled. The React page keeps the operator-provided token only in component memory.

This is intentionally a local, single-operator safeguard. It is not multi-user identity,
authorization, or a suitable public-internet security model.
