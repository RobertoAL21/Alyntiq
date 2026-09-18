# ADR 022 — Require Production Registry State for Model-Driven Paper Orders

## Status

Accepted

## Context

Model lineage already accompanies model-driven strategy proposals and audit records, but
experiment tracking alone does not establish whether a particular artifact and its
evidence are approved for paper trading. Without a durable lifecycle record, any version
string could be sent through the paper-order path.

## Options Considered

### Rely on MLflow experiment names or tags

MLflow stores experiments and artifacts, but it does not provide the explicit lifecycle
contract required by this project and would couple paper eligibility to tracker details.

### Allow any versioned model after backtesting

This relies on caller convention and provides no durable, testable promotion boundary.

### Store lifecycle evidence and gate model-driven paper orders on production

A dedicated registry can retain provenance and evaluation evidence while exposing a small
eligibility interface to execution without merging model, risk, and broker concerns.

## Decision

Create a version-unique model registry with immutable provenance, parameters, metrics,
backtest results, and artifact URI. New records start as `candidate`; only explicit,
validated transitions can make them `production`. A retired model is terminal.

When an approved risk decision has model lineage, `submit_approved_order` requires the
registry eligibility interface and a database session. It queries the registry before
calling the injected paper broker and rejects every state except `production`.

## Consequences

Paper-trading orchestration must supply registry access for model-driven orders, making
unregistered or non-production models fail closed before an external broker request.
Non-model orders preserve the existing execution interface. The registry does not serve
models, evaluate drift, emit telemetry, or add deployment workflows; those concerns remain
in later phases.
