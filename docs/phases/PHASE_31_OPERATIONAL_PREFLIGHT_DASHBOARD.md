# Phase 31 — Operational Preflight Dashboard

## Objective

Make the existing one-shot paper-worker preflight operable from the Models dashboard without
changing the visual language or introducing broker execution.

## Scope

Implement:

- a token-protected backend control endpoint that invokes exactly one worker preflight cycle;
- a structured response with ready/blocked counts and per-deployment results;
- a compact Models-page action to run the check and refresh persisted status;
- clear copy that distinguishes a one-shot safety check from a running trading bot; and
- tests and documentation.

## Explicitly Out of Scope

- daemon workers, schedules, queues, automatic restarts, or an imaginary Start/Stop state;
- model inference, strategy signals, risk decisions, broker access, or order submission;
- live trading and public authentication.

## Safety Invariants

1. The endpoint requires the existing local control token.
2. It delegates only to `PaperWorkerService.run_once` and commits its immutable preflight
   results.
3. It cannot run a loop, contact Alpaca, load an artifact, or change a deployment state.
4. `Disarm` remains the sole UI action that revokes a deployment's future eligibility.
