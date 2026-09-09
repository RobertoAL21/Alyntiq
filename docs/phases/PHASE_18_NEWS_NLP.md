Phase 18 — News and NLP

Objective

Transform financial news into structured signals.

Pipeline

News
→ Deduplication
→ Entity Extraction
→ Ticker Mapping
→ NLP / LLM
→ Structured Signal

Output

* ticker
* sentiment
* event_type
* confidence
* importance

Rule

LLMs must never directly execute trades.

Their output becomes another feature or signal.