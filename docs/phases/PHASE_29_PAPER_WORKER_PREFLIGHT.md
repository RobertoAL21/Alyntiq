# Phase 29 — Paper Worker Preflight

## Objective

Add an explicit, single-cycle paper-worker preflight for `armed` deployments. The worker
must prove that an armed configuration is still eligible at the moment a future runtime
would consume it, and persist an observable result without performing market, model, risk,
or broker work.

## Scope

Implement:

- a durable worker-preflight record linked to a strategy deployment;
- a single-run service that considers only `armed` deployments;
- repeated validation of paper environment, production model state, and model lineage;
- structured `ready` or `blocked` outcomes, with a safe non-secret reason;
- a `python -m scripts.run_paper_worker --once` operator command;
- read-only dashboard visibility of the most recent worker outcome;
- tests, migration, logging, and documentation.

## Explicitly Out of Scope

- daemon processes, schedulers, queues, or automatic restarts;
- model-artifact loading, prediction generation, feature calculation, or signal generation;
- portfolio/account snapshots, risk evaluation, broker polling, cancellation, or order
  submission;
- changing deployment state to `running`, `paused`, `stopped`, or `error`;
- live trading or a public execution API.

## Safety Invariants

1. The command accepts only `--once`; it never loops in the background.
2. Only an `armed` deployment is considered; drafts and validated configurations are ignored.
3. Every candidate is rechecked against `TRADING_ENVIRONMENT=paper`, registry production
   state, and feature/target lineage at run time.
4. A blocked preflight is persisted and does not submit an order or mutate the deployment.
5. A ready preflight is evidence of configuration eligibility only, never evidence of a
   prediction, a risk decision, or trade execution.

## Verification

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend pytest tests/test_paper_worker.py tests/test_run_paper_worker_cli.py
```

## Completion Criteria

- Running the command produces persisted, inspectable results for armed deployments.
- Demoting a model or changing the paper environment blocks the next preflight.
- No code path imports or invokes the broker adapter, risk engine, strategy implementation,
  or model loader.
