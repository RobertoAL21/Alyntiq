# Paper Worker Preflight

## Scope

Phase 29 introduces a single-cycle, non-executing worker boundary for armed paper
deployments:

```text
armed deployment -> runtime eligibility check -> persisted ready | blocked preflight
```

The worker does not cross into the application pipeline beyond deployment eligibility. In
particular, it does not load an artifact, calculate features, obtain a prediction, invoke a
strategy, construct a risk context, inspect a broker account, or submit an order.

## Persistence and operation

Each preflight is immutable and records the deployment, outcome, reason, and timestamp.
The `run_paper_worker` command is intentionally a one-shot process so an operator or future
scheduler owns invocation explicitly. The dashboard reads the latest result only; it cannot
run the command or alter deployment state.

## Runtime gate

The service handles only `armed` deployments and repeats the same paper environment,
production registry, and model-lineage checks used when arming. A failed check produces a
`blocked` result rather than an exception that prevents other armed deployments from being
examined.
