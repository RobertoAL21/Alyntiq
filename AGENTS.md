Alyntiq — AI Agent Instructions

This file defines the rules that any AI coding agent must follow when working on Alyntiq.

Before making any code changes, read:

1. docs/PROJECT_CONTEXT.md
2. docs/CURRENT_PHASE.md
3. docs/ARCHITECTURE.md
4. docs/DEVELOPMENT_GUIDELINES.md
5. The current phase file inside docs/phases/
6. Any relevant ADRs inside docs/decisions/

Do not start coding before understanding the current repository state.

Core Development Rules

* Work only on the current phase.
* Do not implement future phases prematurely.
* Inspect existing code before creating or modifying files.
* Avoid duplicating functionality.
* Prefer simple, modular and maintainable solutions.
* Do not add dependencies without a clear reason.
* Never hardcode secrets or credentials.
* All sensitive values must come from environment variables.
* Add tests for new functionality.
* Run tests and linting after meaningful changes.
* Do not create Git commits unless explicitly requested.
* Update documentation when architecture or behavior changes.
* Do not make assumptions about financial correctness without validation.

Core Architecture Principle

Alyntiq follows this separation:

Market Data
→ Features
→ Models
→ Strategy
→ Risk
→ Execution
→ Portfolio

These layers must remain separated.

Most importantly:

MODEL ≠ STRATEGY ≠ RISK ≠ EXECUTION

A model produces predictions.

A strategy converts predictions and market conditions into proposed actions.

The risk engine decides whether those actions are acceptable.

The execution layer sends approved actions to a simulated broker.

Never merge these responsibilities into one component.

Trading Safety

Alyntiq is designed for:

* research
* historical backtesting
* paper trading

Real-money trading is outside the project scope unless explicitly introduced through a future architectural decision.

The system must default to:

TRADING_ENVIRONMENT=paper

Never default to live execution.