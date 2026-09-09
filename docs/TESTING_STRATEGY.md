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

Every pull request should eventually run:

* linting
* formatting checks
* unit tests
* integration tests where practical
* ML/data sanity checks as those phases are introduced