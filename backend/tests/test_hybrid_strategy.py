from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.backtesting.competition import StrategyCompetitionService
from app.backtesting.portfolio import initial_portfolio
from app.backtesting.types import BacktestBar, BacktestConfig, SignalSide
from app.news import NewsEventType, NewsSentiment, NewsSignal
from app.regimes import MarketRegime, RegimeClassification, VolatilityRegime
from app.strategies.hybrid import (
    HybridStrategy,
    HybridStrategyError,
    HybridStrategyInputs,
    HybridStrategyParameters,
    NewsSentimentStrategy,
    QuantitativeContext,
    build_hybrid_competitors,
)
from app.strategies.ml import ModelPrediction, ThresholdSelection


def timestamp(day: int) -> datetime:
    return datetime(2024, 1, 2, tzinfo=UTC) + timedelta(days=day)


def bar(day: int, close: str) -> BacktestBar:
    price = Decimal(close)
    return BacktestBar(
        timestamp=timestamp(day),
        symbol="AAPL",
        open=price,
        high=price + Decimal("1"),
        low=price - Decimal("1"),
        close=price,
    )


def prediction(day: int, probability: float) -> ModelPrediction:
    return ModelPrediction(timestamp(day), "AAPL", probability, "model-v1", "features-v1")


def context(day: int, trend: float, momentum: float) -> QuantitativeContext:
    return QuantitativeContext(timestamp(day), "AAPL", trend, momentum)


def regime(
    day: int,
    market_regime: MarketRegime = MarketRegime.BULL,
    volatility: VolatilityRegime = VolatilityRegime.LOW,
) -> RegimeClassification:
    return RegimeClassification(timestamp(day), market_regime, volatility, 0, 1.0)


def signal(day: int, sentiment: NewsSentiment = NewsSentiment.POSITIVE) -> NewsSignal:
    return NewsSignal(
        article_id=f"article-{day}",
        published_at=timestamp(day),
        ticker="AAPL",
        sentiment=sentiment,
        event_type=NewsEventType.EARNINGS,
        confidence=1.0,
        importance=0.8,
        analyzer_version="lexicon-news-v1",
    )


def thresholds() -> ThresholdSelection:
    return ThresholdSelection(0.4, 0.6, 0.7, 20, 10)


def inputs(
    predictions: dict[datetime, ModelPrediction],
    contexts: dict[datetime, QuantitativeContext],
    regimes: dict[datetime, RegimeClassification],
    signals: tuple[NewsSignal, ...] = (),
) -> HybridStrategyInputs:
    return HybridStrategyInputs(predictions, contexts, regimes, signals, thresholds())


def test_hybrid_requires_all_favorable_point_in_time_context_for_a_buy() -> None:
    current = bar(0, "100")
    strategy = HybridStrategy(
        inputs(
            {current.timestamp: prediction(0, 0.8)},
            {current.timestamp: context(0, 0.1, 0.1)},
            {current.timestamp: regime(0)},
            (signal(0),),
        ),
        HybridStrategyParameters(quantity=2),
    )

    proposal = strategy.on_bar(current, initial_portfolio(Decimal("1000")))

    assert proposal is not None
    assert proposal.side is SignalSide.BUY
    assert proposal.quantity == 2
    assert proposal.lineage is not None
    assert proposal.lineage.strategy_version == "hybrid-v1"


def test_hybrid_rejects_missing_or_mismatched_context_instead_of_using_future_data() -> None:
    current = bar(0, "100")
    missing = HybridStrategy(
        inputs({current.timestamp: prediction(0, 0.8)}, {}, {current.timestamp: regime(0)}),
        HybridStrategyParameters(quantity=1),
    )
    mismatched_prediction = ModelPrediction(timestamp(0), "MSFT", 0.8, "model-v1", "features-v1")
    mismatched = HybridStrategy(
        inputs(
            {current.timestamp: mismatched_prediction},
            {current.timestamp: context(0, 0.1, 0.1)},
            {current.timestamp: regime(0)},
        ),
        HybridStrategyParameters(quantity=1),
    )

    assert missing.on_bar(current, initial_portfolio(Decimal("1000"))) is None
    with pytest.raises(HybridStrategyError, match="must match"):
        mismatched.on_bar(current, initial_portfolio(Decimal("1000")))


def test_news_strategy_ignores_future_news_until_its_publication_timestamp() -> None:
    strategy = NewsSentimentStrategy((signal(1),), HybridStrategyParameters(quantity=1))
    portfolio = initial_portfolio(Decimal("1000"))

    assert strategy.on_bar(bar(0, "100"), portfolio) is None
    proposal = strategy.on_bar(bar(1, "100"), portfolio)

    assert proposal is not None
    assert proposal.side is SignalSide.BUY


def test_hybrid_competitors_run_under_one_shared_backtest_config() -> None:
    bars = (bar(0, "100"), bar(1, "101"), bar(2, "102"), bar(3, "103"))
    hybrid_inputs = inputs(
        {
            point.timestamp: prediction(index, 0.8 if index == 0 else 0.2)
            for index, point in enumerate(bars)
        },
        {
            point.timestamp: context(
                index, 0.1 if index == 0 else -0.1, 0.1 if index == 0 else -0.1
            )
            for index, point in enumerate(bars)
        },
        {
            point.timestamp: regime(index, MarketRegime.BULL if index == 0 else MarketRegime.BEAR)
            for index, point in enumerate(bars)
        },
        (signal(0),),
    )
    config = BacktestConfig(initial_cash=Decimal("1000"))

    competition = StrategyCompetitionService().run(
        bars,
        config=config,
        competitors=build_hybrid_competitors(hybrid_inputs, HybridStrategyParameters(quantity=1)),
    )

    assert [run.strategy_name for run in competition.runs] == [
        "buy_and_hold",
        "momentum",
        "pure_ml",
        "news_only",
        "hybrid",
    ]
    assert all(run.result.config == config for run in competition.runs)
    assert all(run.result.portfolio.initial_cash == Decimal("1000") for run in competition.runs)
    assert competition.runs[-1].result.metrics.number_of_trades == 1
