Phase 13 — Real-Time Market Data

Objective

Consume live market events.

Technology

Alpaca WebSockets.

Flow

WebSocket
→ Market Consumer
→ Feature Calculation
→ Strategy
→ Risk
→ Broker

Handle

* reconnects
* duplicates
* out-of-order events
* rate limits
* API errors