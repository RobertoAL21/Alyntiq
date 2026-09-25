# Phase 28 — Paper Strategy Activation

## Objective

Add a deliberately limited control plane for preparing a reviewed strategy configuration
for paper trading. It must make configuration and approval visible without starting a
worker, loading a model artifact, polling a broker, or submitting an order.

## Scope

Implement:

- a persistent paper-strategy deployment record;
- the states `draft`, `validated`, and `armed` only;
- immutable model, feature, target, strategy, market-data, threshold, symbol, quantity,
  and risk-limit configuration after creation;
- validation that requires `TRADING_ENVIRONMENT=paper`, a registered `production` model,
  matching feature and target lineage, and every supported risk limit to be explicitly set;
- a local control-token gate for mutating API endpoints;
- read-only deployment status and dashboard controls for create, validate, arm, and disarm;
- tests, migration, and operator documentation.

## Explicitly Out of Scope

- background workers, schedules, or automatic activation;
- model artifact loading or inference;
- signal generation, risk evaluation, broker polling, or order submission;
- live trading, broker endpoints, or public multi-user authentication;
- any transition to `running`, `paused`, `stopped`, or `error`.

## Safety Invariants

1. `TRADING_ENVIRONMENT` remains `paper`; a non-paper setting rejects validation and arm.
2. Only a registry model in `production` may be validated or armed.
3. Model feature and target versions must exactly match the deployment configuration.
4. All eight supported `RiskLimits` fields are required for a deployment; none can silently
   be disabled.
5. A token from `DASHBOARD_CONTROL_TOKEN` is required for every mutation. The browser keeps
   the supplied value only in memory and never persists or displays it.
6. `armed` is an approved configuration state, not execution authority.

## State Machine

```text
draft --validate--> validated --arm--> armed
                     ^                |
                     +----disarm------+ 
```

`validate` and `arm` repeat the paper, registry, lineage, and risk checks. Disarming returns
an armed record to `validated`; it never triggers an execution side effect.

## Verification

From the repository root:

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend pytest tests/test_strategy_deployments.py tests/test_strategy_deployment_api.py
docker compose exec frontend npm test -- --run
```

## Completion Criteria

- A user can inspect and prepare a deployment from the Models dashboard.
- Invalid or unreviewed configurations cannot be armed.
- The project remains paper-only and no new path contacts Alpaca.
