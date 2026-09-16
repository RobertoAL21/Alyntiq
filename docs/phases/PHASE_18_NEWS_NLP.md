Phase 18 — News and NLP

Status: COMPLETE

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

Delivered:

* immutable, publication-time news-article values and deterministic content deduplication;
* conservative entity extraction and ticker mapping for the initial supported symbols;
* a transparent lexical NLP baseline that produces sentiment, event type, confidence, and
  importance; and
* one structured research signal per mapped ticker, with analyzer-version lineage.

No news analyzer can propose or execute a trade. A future LLM adapter may implement the
same analysis interface, but it must remain confined to structured research context.
