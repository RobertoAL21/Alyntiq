from collections.abc import Sequence

from app.news.analyzer import LexiconNewsAnalyzer, NewsAnalyzer
from app.news.mapping import TickerMapper
from app.news.types import NewsArticle, NewsProcessingResult, NewsSignal


class NewsSignalService:
    """Create deduplicated, ticker-mapped research signals without trading side effects."""

    def __init__(
        self,
        *,
        ticker_mapper: TickerMapper | None = None,
        analyzer: NewsAnalyzer | None = None,
    ) -> None:
        self._ticker_mapper = ticker_mapper or TickerMapper()
        self._analyzer = analyzer or LexiconNewsAnalyzer()

    def process(self, articles: Sequence[NewsArticle]) -> NewsProcessingResult:
        """Deduplicate content, map known entities, then produce one signal per ticker."""
        articles = tuple(articles)
        unique_articles = deduplicate_articles(articles)
        signals: list[NewsSignal] = []
        for article in unique_articles:
            entities = self._ticker_mapper.extract(article)
            if not entities:
                continue
            analysis = self._analyzer.analyze(article, entities)
            for ticker in sorted({entity.ticker for entity in entities}):
                signals.append(
                    NewsSignal(
                        article_id=article.id,
                        published_at=article.published_at,
                        ticker=ticker,
                        sentiment=analysis.sentiment,
                        event_type=analysis.event_type,
                        confidence=analysis.confidence,
                        importance=analysis.importance,
                        analyzer_version=analysis.analyzer_version,
                    )
                )
        return NewsProcessingResult(
            received_article_count=len(articles),
            unique_article_count=len(unique_articles),
            signals=tuple(signals),
        )


def deduplicate_articles(articles: Sequence[NewsArticle]) -> tuple[NewsArticle, ...]:
    """Keep the earliest stable article for each normalized title-and-body fingerprint."""
    retained: dict[str, NewsArticle] = {}
    for article in sorted(articles, key=lambda candidate: (candidate.published_at, candidate.id)):
        retained.setdefault(article.fingerprint, article)
    return tuple(retained.values())
