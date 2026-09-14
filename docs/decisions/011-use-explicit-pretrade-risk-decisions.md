# ADR 011: Use explicit pre-trade risk decisions

## Status

Accepted

## Context

Strategies produce trade proposals, but a proposal must not itself decide position caps,
loss limits, cash reserves, or protective exits. Mixing those responsibilities would make
historical results difficult to audit and would couple model or strategy code to risk
policy.

The existing simulator executes a pending order on the next available bar open. Any risk
integration must preserve that timing and remain independent from brokers and portfolio
systems planned for later phases.

## Decision

Create a pure `app.risk` package with immutable proposed-order, context, limit, and
decision value objects. `RiskEngine` evaluates a proposal against explicitly configured
limits and returns a `RiskDecision` that includes the original and, where applicable,
reduced order.

The backtest engine optionally supplies a completed-bar risk context before queuing a
strategy order. Stop-loss and take-profit protection are evaluated at the completed close
and become a sell proposal for next-open execution. No limit is enabled unless a caller
sets it.

## Consequences

- Strategy, risk policy, accounting, and execution remain separate layers.
- Backtests can test and explain accepted, reduced, and rejected orders deterministically.
- Daily loss is currently realized-PnL based, and stop/take protection is close-triggered;
  neither should be represented as intraday or broker-native behavior.
- A future multi-asset portfolio engine can provide a richer risk context without moving
  policy into a strategy or broker adapter.
