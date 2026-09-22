Alyntiq — Testing Strategy

Testing Layers

Unit Tests

Test isolated logic.

Examples:

* feature calculations
* risk rules
* position calculations
* metrics

Integration Tests

Test interactions between components.

Examples:

* database repositories
* API endpoints
* broker adapters
* ingestion pipelines

Data Quality Tests

Validate market data.

Examples:

* no negative prices
* timestamps valid
* no unexpected duplicates
* OHLC consistency

Basic rule:

low <= open <= high

low <= close <= high

Leakage Tests

Validate that feature pipelines do not use future values.

Backtesting Sanity Tests

Examples:

* no trades before data exists
* portfolio cash cannot become invalid without leverage
* trade fills happen at valid timestamps
* no future price is used for current decisions

API Tests

Validate:

* status codes
* schemas
* validation
* failure handling

CI Requirements

Every pull request runs:

* linting
* formatting checks
* unit tests
* the complete backend pytest suite
* frontend lint, tests, and production build
* explicit feature-leakage, walk-forward, model-version, paper-broker, and backtesting
  sanity checks
* backend and frontend Docker image builds
* tracked-file and paper-trading safety verification

Image publication and deployment are deliberately not part of CI until protected external
environments and credentials are explicitly configured.
