Architecture Decision Records

Use this directory for important architectural decisions.

Suggested naming:

001-paper-trading-only.md
002-use-alpaca.md
003-walk-forward-validation.md

Implemented decisions also include:

016-keep-dashboard-presentation-only-until-read-apis-exist.md
017-run-strategy-competitions-with-isolated-fresh-backtests.md
018-keep-market-regimes-descriptive-and-training-period-bound.md
019-keep-news-analysis-structured-and-trade-independent.md
020-compose-hybrid-strategies-from-point-in-time-context.md
021-evaluate-temporal-models-with-symbol-local-windows.md
022-require-production-registry-state-for-model-paper-orders.md
023-use-opentelemetry-with-optional-otlp-export.md
024-detect-drift-against-fixed-reference-samples.md
025-use-separate-unprivileged-web-runtime-images.md
026-keep-ci-release-free-of-credentials.md
027-expose-persisted-research-data-through-read-only-dashboard-apis.md
028-keep-dashboard-activation-as-a-paper-only-control-plane.md

Each ADR should contain:

Decision

Context

Why was this decision required?

Options Considered

What alternatives existed?

Decision

What did we choose?

Reasons

Why?

Consequences

What tradeoffs does this introduce?
