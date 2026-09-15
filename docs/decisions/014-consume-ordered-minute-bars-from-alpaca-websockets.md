# ADR 014: Consume ordered minute bars from Alpaca WebSockets

## Status

Accepted

## Context

Phase 13 introduces real-time market data. Alpaca's WebSocket stream can contain control
messages, batches of market events, transient connection failures, connection-limit errors,
and bars that arrive more than once or after a newer timestamp. Downstream feature and
strategy code must not silently treat an out-of-order event as a new observation.

## Decision

Create a dedicated asynchronous market-data consumer for Alpaca's completed one-minute bar
channel. Authenticate and subscribe through the documented WebSocket message protocol using
the existing credentials and selected IEX/SIP feed.

Maintain the latest yielded timestamp per symbol and drop events at or before that timestamp.
Retry disconnections and Alpaca connection-limit error `406` using bounded exponential
backoff. Raise authentication, malformed-protocol, and other provider errors to the caller.

## Consequences

- Real-time data remains separate from feature calculation, strategy, risk, execution, and
  persistence.
- Consumers receive a monotonic stream of immutable completed bars per symbol.
- Late `updatedBars` corrections are deliberately not applied; future persistence or feature
  revisions require an explicit correction policy.
- The default retry limit prevents an unavailable stream from retrying indefinitely without
  caller visibility.
