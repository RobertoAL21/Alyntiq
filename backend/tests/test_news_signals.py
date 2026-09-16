from datetime import UTC, datetime, timedelta

from app.news import (
    LexiconNewsAnalyzer,
    NewsArticle,
    NewsEventType,
    NewsSentiment,
    NewsSignalService,
    TickerMapper,
    deduplicate_articles,
)


def article(
    identifier: str,
    title: str,
    body: str = "",
    *,
    minutes: int = 0,
) -> NewsArticle:
    return NewsArticle(
        id=identifier,
        published_at=datetime(2024, 1, 2, tzinfo=UTC) + timedelta(minutes=minutes),
        source="example-news",
        title=title,
        body=body,
        url=f"https://example.test/{identifier}",
    )


def test_deduplication_normalizes_content_and_retains_the_earliest_article() -> None:
    first = article("first", "Apple beats earnings", " Revenue shows growth. ")
    duplicate = article("later", " apple   beats earnings ", "revenue shows growth.", minutes=1)

    unique = deduplicate_articles((duplicate, first))

    assert unique == (first,)


def test_mapper_extracts_known_company_names_and_explicit_supported_tickers_only() -> None:
    mapper = TickerMapper()
    entities = mapper.extract(article("news-1", "Apple and $MSFT announce product news for XYZ"))

    assert [(entity.ticker, entity.mention) for entity in entities] == [
        ("AAPL", "Apple"),
        ("MSFT", "$MSFT"),
    ]


def test_lexicon_analyzer_returns_transparent_structured_context() -> None:
    analyzed = LexiconNewsAnalyzer().analyze(
        article("news-1", "Apple beats earnings and raises guidance"),
        TickerMapper().extract(article("news-1", "Apple beats earnings and raises guidance")),
    )

    assert analyzed.sentiment is NewsSentiment.POSITIVE
    assert analyzed.event_type is NewsEventType.EARNINGS
    assert analyzed.confidence == 1.0
    assert analyzed.importance == 0.9
    assert analyzed.analyzer_version == "lexicon-news-v1"


def test_service_emits_one_research_signal_per_known_ticker_after_deduplication() -> None:
    original = article("original", "Apple beats earnings while Microsoft reports a loss")
    duplicate = article(
        "duplicate", " apple beats earnings while microsoft reports a loss ", minutes=2
    )
    service = NewsSignalService()

    result = service.process((duplicate, original, article("unmapped", "XYZ announces a launch")))

    assert result.received_article_count == 3
    assert result.unique_article_count == 2
    assert result.duplicate_article_count == 1
    assert [signal.article_id for signal in result.signals] == ["original", "original"]
    assert [signal.ticker for signal in result.signals] == ["AAPL", "MSFT"]
    assert all(signal.event_type is NewsEventType.EARNINGS for signal in result.signals)
    assert all(signal.sentiment is NewsSentiment.NEUTRAL for signal in result.signals)
    assert all(signal.analyzer_version == "lexicon-news-v1" for signal in result.signals)
