# ADR 002 — Centralize Runtime Configuration with a Paper-Trading Default

## Status

Accepted

## Context

Alyntiq needs configuration for application behavior, infrastructure connections, and
future provider credentials. Reading environment variables throughout the application
would make configuration difficult to validate, test, and audit.

The platform is limited to research, backtesting, and paper trading. Real-money
execution must not be enabled accidentally.

## Options Considered

### Read environment variables at each use site

This keeps setup local but duplicates parsing and validation and can cause different
parts of the application to interpret the same value differently.

### Centralized typed runtime settings

Load environment variables once through a typed settings object and pass or import
that configuration where needed.

## Decision

Use `app.core.config.Settings`, backed by Pydantic Settings, as the centralized source
of runtime configuration.

Configuration is supplied through environment variables or a local `.env` file, which
is excluded from version control. `TRADING_ENVIRONMENT` defaults to `paper`.

No execution capability exists in Phase 0. Any future real-money execution requires a
separate architecture decision and safeguards before it can be implemented.

## Consequences

Application modules do not access environment variables directly.

Configuration has explicit types and can be unit-tested without external services.

Developers can override local settings through `.env` while secrets remain untracked.
