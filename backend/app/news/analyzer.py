import re
from collections.abc import Sequence
from typing import Protocol

from app.news.types import NewsAnalysis, NewsArticle, NewsEntity, NewsEventType, NewsSentiment

POSITIVE_TERMS = frozenset(
    {"beat", "beats", "growth", "raise", "raises", "record", "approval", "profit"}
)
NEGATIVE_TERMS = frozenset(
    {"cut", "cuts", "decline", "loss", "miss", "misses", "lawsuit", "investigation"}
)
EVENT_PATTERNS: tuple[tuple[NewsEventType, re.Pattern[str]], ...] = (
    (
        NewsEventType.MERGER_AND_ACQUISITION,
        re.compile(r"\b(acquire|acquisition|merge|merger)\b", re.I),
    ),
    (NewsEventType.EARNINGS, re.compile(r"\b(earnings|revenue|quarterly results)\b", re.I)),
    (NewsEventType.GUIDANCE, re.compile(r"\b(guidance|outlook|forecast)\b", re.I)),
    (NewsEventType.REGULATION, re.compile(r"\b(regulator|regulation|antitrust|sec)\b", re.I)),
    (NewsEventType.PRODUCT, re.compile(r"\b(product|launch|release)\b", re.I)),
)
EVENT_IMPORTANCE = {
    NewsEventType.MERGER_AND_ACQUISITION: 0.70,
    NewsEventType.EARNINGS: 0.60,
    NewsEventType.GUIDANCE: 0.55,
    NewsEventType.REGULATION: 0.55,
    NewsEventType.PRODUCT: 0.35,
    NewsEventType.OTHER: 0.20,
}


class NewsAnalyzer(Protocol):
    """Analyze content into structured context; implementations cannot create trade actions."""

    def analyze(self, article: NewsArticle, entities: Sequence[NewsEntity]) -> NewsAnalysis: ...


class LexiconNewsAnalyzer:
    """A transparent, deterministic NLP baseline for Phase 18 research signals."""

    version = "lexicon-news-v1"

    def analyze(self, article: NewsArticle, entities: Sequence[NewsEntity]) -> NewsAnalysis:
        tokens = re.findall(r"[a-z]+", article.text.casefold())
        positive = sum(token in POSITIVE_TERMS for token in tokens)
        negative = sum(token in NEGATIVE_TERMS for token in tokens)
        sentiment = _sentiment(positive, negative)
        confidence = (
            0.0 if positive + negative == 0 else abs(positive - negative) / (positive + negative)
        )
        event_type = next(
            (event_type for event_type, pattern in EVENT_PATTERNS if pattern.search(article.text)),
            NewsEventType.OTHER,
        )
        importance = min(
            1.0, EVENT_IMPORTANCE[event_type] + confidence * 0.25 + len(entities) * 0.05
        )
        return NewsAnalysis(sentiment, event_type, confidence, importance, self.version)


def _sentiment(positive: int, negative: int) -> NewsSentiment:
    if positive > negative:
        return NewsSentiment.POSITIVE
    if negative > positive:
        return NewsSentiment.NEGATIVE
    return NewsSentiment.NEUTRAL
