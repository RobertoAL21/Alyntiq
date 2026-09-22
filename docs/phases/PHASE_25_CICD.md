Phase 25 — CI/CD

Status: COMPLETE

Pull Requests

Run:

* lint
* unit tests
* integration tests
* feature tests
* leakage tests
* backtesting sanity tests
* Docker builds

Main Branch

Potentially:

* build
* push image
* deploy

Add safety checks:

* no live credentials
* no leakage
* model version required
* paper environment enforcement

Delivered:

* separate backend, frontend, financial-safety, and Docker-build validation jobs for pull
  requests, `main` pushes, and manual runs;
* tracked-file, safe-placeholder, paper-environment, paper-endpoint, and model-lineage
  CI guards; and
* explicit leakage, paper-broker, model-version, and backtesting safety test selection.

Image publication, migration execution, and deployment remain disabled until a protected
registry, environment, and runtime secrets are explicitly authorized.
