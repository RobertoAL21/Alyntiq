"""Deterministic, structured financial-news research signals."""

from app.news.analyzer import LexiconNewsAnalyzer, NewsAnalyzer
from app.news.mapping import DEFAULT_TICKER_ALIASES, TickerMapper
from app.news.service import NewsSignalService, deduplicate_articles
from app.news.types import (
    NewsAnalysis,
    NewsArticle,
    NewsEntity,
    NewsEventType,
    NewsProcessingResult,
    NewsSentiment,
    NewsSignal,
)

__all__ = [
    "DEFAULT_TICKER_ALIASES",
    "LexiconNewsAnalyzer",
    "NewsAnalysis",
    "NewsAnalyzer",
    "NewsArticle",
    "NewsEntity",
    "NewsEventType",
    "NewsProcessingResult",
    "NewsSentiment",
    "NewsSignal",
    "NewsSignalService",
    "TickerMapper",
    "deduplicate_articles",
]
