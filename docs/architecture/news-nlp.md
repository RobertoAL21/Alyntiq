# News and NLP

## Scope

Phase 18 provides a pure `app.news` pipeline that converts already supplied news articles
into structured research signals. It has no provider integration, database persistence,
HTTP endpoint, background worker, model training, strategy implementation, risk decision,
or broker interaction.

```text
published article -> normalized content deduplication -> known entity/ticker mapping
                                                           |
                                                           v
                                            deterministic NLP analysis -> research signal
```

## Article and entity contract

`NewsArticle` requires a source-supplied id, timezone-aware publication timestamp, source,
title, and URL. Its content fingerprint is a SHA-256 hash of normalized title and body.
`deduplicate_articles` retains the earliest article by publication time and id for each
fingerprint, so the same content cannot inflate the resulting signals.

`TickerMapper` only recognizes configured company aliases and explicit mentions of the
initial supported tickers: AAPL, MSFT, NVDA, SPY, and QQQ. It deliberately does not infer
unknown all-caps words as securities, avoiding unsupported ticker guesses.

## NLP and signals

The `NewsAnalyzer` protocol is an analysis-only boundary. The initial
`LexiconNewsAnalyzer` is deterministic and versioned as `lexicon-news-v1`; it counts a
small documented positive/negative term set and recognizes earnings, guidance, merger and
acquisition, regulation, and product events. It returns:

- sentiment: positive, neutral, or negative;
- event type;
- confidence in the lexical polarity; and
- importance, a bounded context score based on event, confidence, and mapped mentions.

`NewsSignalService` creates one `NewsSignal` per unique mapped ticker, retaining article
publication time and analyzer version. A signal is research context only: it is neither a
model prediction, proposed order, risk approval, nor execution request.

An LLM-backed analyzer can be introduced later only by implementing `NewsAnalyzer` and
returning the same validated `NewsAnalysis` value. It cannot receive an execution client
through this package.

## Verification

From `backend/`, run:

```bash
ruff format --check .
ruff check .
pytest tests/test_news_signals.py
```
