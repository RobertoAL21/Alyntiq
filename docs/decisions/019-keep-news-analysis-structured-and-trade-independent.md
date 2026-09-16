# ADR 019: Keep news analysis structured and trade independent

## Status

Accepted

## Context

News content is often duplicated, ambiguous, and not intrinsically a trade instruction.
Allowing an NLP or LLM component to select tickers freely or invoke strategy, risk, or
execution code would make its outputs difficult to reproduce and would violate the
project's domain boundaries.

## Decision

Create a pure news pipeline that accepts already supplied articles, deduplicates normalized
content, maps only an explicit alias/ticker allowlist, and returns validated structured
signals. The initial analyzer is a deterministic lexical baseline with a version value.
An LLM adapter may later implement the analysis protocol, but can only return the same
`NewsAnalysis` value object.

## Consequences

* News experiments have stable content, timestamp, ticker, and analyzer-version lineage.
* Unknown uppercase words are not silently treated as securities.
* Sentiment and importance are research context, not investment advice, strategy proposals,
  risk decisions, or orders.
* News-provider ingestion, persistence, LLM selection, and validation of trading impact
  remain future work.
