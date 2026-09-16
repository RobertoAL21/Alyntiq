import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from math import isfinite


class NewsSentiment(StrEnum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class NewsEventType(StrEnum):
    EARNINGS = "earnings"
    GUIDANCE = "guidance"
    MERGER_AND_ACQUISITION = "merger_and_acquisition"
    REGULATION = "regulation"
    PRODUCT = "product"
    OTHER = "other"


@dataclass(frozen=True)
class NewsArticle:
    """A source-supplied news article available at its published timestamp."""

    id: str
    published_at: datetime
    source: str
    title: str
    body: str
    url: str

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("news article id must not be blank")
        if self.published_at.tzinfo is None or self.published_at.utcoffset() is None:
            raise ValueError("news article published_at must include a timezone")
        if not self.source.strip():
            raise ValueError("news article source must not be blank")
        if not self.title.strip():
            raise ValueError("news article title must not be blank")
        if not self.url.strip():
            raise ValueError("news article url must not be blank")
        object.__setattr__(self, "id", self.id.strip())
        object.__setattr__(self, "published_at", self.published_at.astimezone(UTC))
        object.__setattr__(self, "source", self.source.strip())
        object.__setattr__(self, "title", self.title.strip())
        object.__setattr__(self, "body", self.body.strip())
        object.__setattr__(self, "url", self.url.strip())

    @property
    def fingerprint(self) -> str:
        """Stable content fingerprint used only for deterministic deduplication."""
        return sha256(_normalized_text(f"{self.title}\n{self.body}").encode()).hexdigest()

    @property
    def text(self) -> str:
        return f"{self.title}\n{self.body}"


@dataclass(frozen=True)
class NewsEntity:
    ticker: str
    mention: str

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[A-Z]{1,5}", self.ticker.strip().upper()):
            raise ValueError("news entity ticker must be a one-to-five-letter symbol")
        if not self.mention.strip():
            raise ValueError("news entity mention must not be blank")
        object.__setattr__(self, "ticker", self.ticker.strip().upper())
        object.__setattr__(self, "mention", self.mention.strip())


@dataclass(frozen=True)
class NewsAnalysis:
    """Structured NLP output, independent from strategies and execution."""

    sentiment: NewsSentiment
    event_type: NewsEventType
    confidence: float
    importance: float
    analyzer_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.sentiment, NewsSentiment):
            raise ValueError("news sentiment must be a supported NewsSentiment")
        if not isinstance(self.event_type, NewsEventType):
            raise ValueError("news event_type must be a supported NewsEventType")
        for name in ("confidence", "importance"):
            value = getattr(self, name)
            if not isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"news {name} must be a finite value between 0 and 1")
        if not self.analyzer_version.strip():
            raise ValueError("news analyzer_version must not be blank")
        object.__setattr__(self, "analyzer_version", self.analyzer_version.strip())


@dataclass(frozen=True)
class NewsSignal:
    """One research signal for a mapped ticker, never an order or trade proposal."""

    article_id: str
    published_at: datetime
    ticker: str
    sentiment: NewsSentiment
    event_type: NewsEventType
    confidence: float
    importance: float
    analyzer_version: str

    def __post_init__(self) -> None:
        if not self.article_id.strip():
            raise ValueError("news signal article_id must not be blank")
        if self.published_at.tzinfo is None or self.published_at.utcoffset() is None:
            raise ValueError("news signal published_at must include a timezone")
        NewsEntity(self.ticker, self.ticker)
        NewsAnalysis(
            self.sentiment,
            self.event_type,
            self.confidence,
            self.importance,
            self.analyzer_version,
        )
        object.__setattr__(self, "article_id", self.article_id.strip())
        object.__setattr__(self, "published_at", self.published_at.astimezone(UTC))
        object.__setattr__(self, "ticker", self.ticker.strip().upper())
        object.__setattr__(self, "analyzer_version", self.analyzer_version.strip())


@dataclass(frozen=True)
class NewsProcessingResult:
    received_article_count: int
    unique_article_count: int
    signals: tuple[NewsSignal, ...]

    @property
    def duplicate_article_count(self) -> int:
        return self.received_article_count - self.unique_article_count


def _normalized_text(value: str) -> str:
    return " ".join(value.casefold().split())
