# ADR 008 — Execute Backtest Signals at the Next Bar Open

## Status

Accepted

## Context

A strategy observing the completed close of a historical bar cannot legitimately decide
after that close and also fill at the same close. Doing so would let a backtest use a
price that was unavailable when the action had to be submitted.

Phase 7 needs a simple, deterministic execution rule that supports slippage and
commission while preserving the separation of strategy, execution, and portfolio
accounting.

## Options Considered

### Fill at the current bar close

This is concise, but it permits same-bar close look-ahead for a strategy that observes
the completed bar.

### Fill at the next available bar open

This submits an order after the current bar closes and fills it only when a later market
price is available.

### Add intraday execution and order-book simulation

This could model more execution details, but requires data and assumptions outside the
daily historical engine in Phase 7.

## Decision

Phase 7 emits a signal after a completed bar and creates a pending order. That order is
filled at the next available bar's open, adjusted unfavorably for configured directional
slippage. Commission is charged as a configurable percentage of fill notional.

The last-bar pending order is cancelled. The initial engine is single-symbol and
long-only. It rejects fills that would make cash negative or sell more shares than are
held; these are accounting constraints and do not replace the future risk engine.

## Consequences

The simulator avoids same-bar-close look-ahead and makes execution costs visible. It does
not model intraday behavior, liquidity, partial fills, short selling, leverage, or broker
semantics. Backtest results remain research outputs rather than guarantees or paper-trade
results.
