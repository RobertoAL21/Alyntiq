Alyntiq — Development Guidelines

General Rules

Prefer:

* readability
* explicit interfaces
* type safety
* small modules
* testability
* reproducibility

Avoid:

* unnecessary abstractions
* premature microservices
* premature optimization
* dependency bloat
* speculative architecture

Phase-Based Development

Alyntiq is developed incrementally.

Every phase must:

1. Have a clear objective.
2. Define its scope.
3. Define what must not be implemented.
4. Add tests.
5. Update documentation.
6. Pass linting.
7. Pass existing tests.
8. Meet its Definition of Done.

Do not begin the next phase before validating the current phase.

Repository Hygiene

Do not commit:

* .env
* secrets
* API keys
* private certificates
* large generated datasets
* model artifacts unless intentionally versioned
* temporary logs

Dependencies

Before adding a dependency, determine:

* what problem it solves
* whether the standard library can solve it
* whether an existing dependency already solves it
* whether the package is actively maintained

Configuration

Runtime configuration should come from environment variables.

Application configuration should be centralized.

Avoid scattered direct environment variable access.

Database

Use migrations for schema changes.

Do not manually modify production schemas.

Indexes must have a clear query reason.

Error Handling

Avoid swallowing exceptions.

Errors should include enough context to investigate failures.

Do not expose secrets through error messages.

Logging

Prefer structured logs.

Important actions should include relevant identifiers.

Examples:

symbol
model_version
strategy_version
order_id
trade_id