# ADR 026 — Keep CI Release-Free Until Deployment Authority Exists

## Status

Accepted

## Context

Alyntiq needs automated pull-request validation for code quality, data-leakage evidence,
paper-trading constraints, and deployable images. The repository has no configured image
registry, cloud account, deployment environment, protected approval gate, or runtime
secrets that authorize a real release.

## Options Considered

### Push and deploy from `main` with placeholder configuration

This risks publishing unreviewed images or creating a deployment path whose credentials,
environment protection, and paper-trading configuration cannot be verified.

### Keep CI limited to generic lint and tests

This would omit frontend validation, image-build verification, and explicit financial
safety evidence required before a later release workflow can be trusted.

### Validate and build continuously, defer publishing and deployment

This creates evidence for every change while keeping external state changes outside the
repository's current authority.

## Decision

Run independent backend, frontend, financial-safety, and Docker-build jobs for pull
requests, `main` pushes, and manual runs. Give the workflow read-only repository
permissions. Do not configure image pushes, migrations, cloud deployment, or secrets in
GitHub Actions.

## Consequences

Every merge candidate has automated quality, leakage, paper-environment, model-lineage,
backtesting, and image-build evidence. Releasing still requires an explicit future
workflow with protected environments, immutable image tags, an external secret manager,
one-off migrations, and post-deployment health verification.
