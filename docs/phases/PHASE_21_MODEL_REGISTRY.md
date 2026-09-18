Phase 21 — Model Registry

Status: COMPLETE

States

* candidate
* staging
* production
* retired

Only production models may run in paper trading.

Record:

* dataset
* feature version
* target version
* parameters
* metrics
* backtest results
* artifact

Delivered:

* a persistent, version-unique registry record with immutable provenance, parameters,
  predictive metrics, backtest results, and artifact URI;
* candidate, staging, production, and retired lifecycle states with explicit allowed
  transitions and a terminal retired state;
* CLI commands to register a candidate and transition a version; and
* a production-only registry gate before an approved model-driven paper order reaches the
  injected broker.

The registry records reviewed evidence; it does not train, serve, deploy, monitor, or
automatically select a model.
