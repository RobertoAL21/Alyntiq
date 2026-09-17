from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from math import isfinite

from app.backtesting.competition import StrategyCompetitor
from app.backtesting.types import BacktestBar, Portfolio, Signal, SignalLineage, SignalSide
from app.news.types import NewsSentiment, NewsSignal
from app.regimes.types import MarketRegime, RegimeClassification, VolatilityRegime
from app.strategies.baselines import BuyAndHoldStrategy, MomentumStrategy
from app.strategies.ml import (
    MLStrategyParameters,
    MLThresholdStrategy,
    ModelPrediction,
    ThresholdSelection,
    classify_probability,
)


class HybridStrategyError(ValueError):
    """Raised when point-in-time hybrid research inputs are inconsistent."""


@dataclass(frozen=True)
class QuantitativeContext:
    """Point-in-time quantitative confirmation supplied to a hybrid strategy."""

    timestamp: datetime
    symbol: str
    trend: float
    momentum: float

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise HybridStrategyError("quantitative context timestamps must include a timezone")
        if not self.symbol.strip():
            raise HybridStrategyError("quantitative context symbol must not be blank")
        if not isfinite(self.trend) or not isfinite(self.momentum):
            raise HybridStrategyError("quantitative context trend and momentum must be finite")
        object.__setattr__(self, "timestamp", self.timestamp.astimezone(UTC))
        object.__setattr__(self, "symbol", self.symbol.strip().upper())


@dataclass(frozen=True)
class HybridStrategyParameters:
    quantity: int
    momentum_window: int = 20
    news_lookback_days: int = 3
    news_score_threshold: float = 0.20
    strategy_version: str = "hybrid-v1"

    def __post_init__(self) -> None:
        if self.quantity < 1:
            raise HybridStrategyError("hybrid quantity must be at least 1")
        if self.momentum_window < 1:
            raise HybridStrategyError("hybrid momentum_window must be positive")
        if self.news_lookback_days < 0:
            raise HybridStrategyError("hybrid news_lookback_days must not be negative")
        if not isfinite(self.news_score_threshold) or not 0 <= self.news_score_threshold <= 1:
            raise HybridStrategyError("hybrid news_score_threshold must be between 0 and 1")
        if not self.strategy_version.strip():
            raise HybridStrategyError("hybrid strategy_version must not be blank")


@dataclass(frozen=True)
class HybridStrategyInputs:
    """All externally prepared, point-in-time research inputs for one hybrid run."""

    predictions: Mapping[datetime, ModelPrediction]
    quantitative_contexts: Mapping[datetime, QuantitativeContext]
    regimes: Mapping[datetime, RegimeClassification]
    news_signals: Sequence[NewsSignal]
    thresholds: ThresholdSelection

    def __post_init__(self) -> None:
        _validate_index("prediction", self.predictions)
        _validate_index("quantitative context", self.quantitative_contexts)
        _validate_index("regime", self.regimes)


@dataclass
class NewsSentimentStrategy:
    """Convert already-structured news context into a long-only research proposal."""

    signals: Sequence[NewsSignal]
    parameters: HybridStrategyParameters

    def on_bar(self, bar: BacktestBar, portfolio: Portfolio) -> Signal | None:
        score = _news_score(bar, self.signals, self.parameters.news_lookback_days)
        if score >= self.parameters.news_score_threshold and portfolio.position is None:
            return Signal(bar.timestamp, bar.symbol, SignalSide.BUY, self.parameters.quantity)
        if score <= -self.parameters.news_score_threshold and portfolio.position is not None:
            return Signal(bar.timestamp, bar.symbol, SignalSide.SELL, portfolio.position.quantity)
        return None


@dataclass
class HybridStrategy:
    """Combine supplied ML, quantitative, regime, and news context into proposals only."""

    inputs: HybridStrategyInputs
    parameters: HybridStrategyParameters

    def on_bar(self, bar: BacktestBar, portfolio: Portfolio) -> Signal | None:
        prediction = self.inputs.predictions.get(bar.timestamp)
        quantitative = self.inputs.quantitative_contexts.get(bar.timestamp)
        regime = self.inputs.regimes.get(bar.timestamp)
        if prediction is None or quantitative is None or regime is None:
            return None
        if prediction.symbol != bar.symbol or quantitative.symbol != bar.symbol:
            raise HybridStrategyError("hybrid inputs must match the backtest bar symbol")

        model_side = classify_probability(
            prediction.up_probability,
            sell_threshold=self.inputs.thresholds.sell_threshold,
            buy_threshold=self.inputs.thresholds.buy_threshold,
        )
        news_score = _news_score(bar, self.inputs.news_signals, self.parameters.news_lookback_days)
        lineage = SignalLineage(
            model_version=prediction.model_version,
            strategy_version=self.parameters.strategy_version,
            feature_version=prediction.feature_version,
            up_probability=prediction.up_probability,
        )
        if portfolio.position is None and _buy_confirmed(
            model_side, quantitative, regime, news_score
        ):
            return Signal(
                bar.timestamp, bar.symbol, SignalSide.BUY, self.parameters.quantity, lineage
            )
        if portfolio.position is not None and _sell_confirmed(
            model_side, quantitative, regime, news_score, self.parameters.news_score_threshold
        ):
            return Signal(
                bar.timestamp,
                bar.symbol,
                SignalSide.SELL,
                portfolio.position.quantity,
                lineage,
            )
        return None


def build_hybrid_competitors(
    inputs: HybridStrategyInputs,
    parameters: HybridStrategyParameters,
) -> tuple[StrategyCompetitor, ...]:
    """Create fresh, comparable Phase 19 competitors for the shared competition service."""
    return (
        StrategyCompetitor("buy_and_hold", lambda: BuyAndHoldStrategy(parameters.quantity)),
        StrategyCompetitor(
            "momentum",
            lambda: MomentumStrategy(parameters.quantity, window=parameters.momentum_window),
        ),
        StrategyCompetitor(
            "pure_ml",
            lambda: MLThresholdStrategy(
                inputs.predictions,
                MLStrategyParameters(parameters.quantity),
                inputs.thresholds,
            ),
        ),
        StrategyCompetitor(
            "news_only",
            lambda: NewsSentimentStrategy(inputs.news_signals, parameters),
        ),
        StrategyCompetitor("hybrid", lambda: HybridStrategy(inputs, parameters)),
    )


def _validate_index(name: str, values: Mapping[datetime, object]) -> None:
    for timestamp, value in values.items():
        if getattr(value, "timestamp", None) != timestamp:
            raise HybridStrategyError(
                f"{name} keys must match their point-in-time value timestamps"
            )


def _news_score(bar: BacktestBar, signals: Sequence[NewsSignal], lookback_days: int) -> float:
    earliest = bar.timestamp - timedelta(days=lookback_days)
    score = 0.0
    for signal in signals:
        if signal.ticker != bar.symbol or not earliest <= signal.published_at <= bar.timestamp:
            continue
        direction = {
            NewsSentiment.POSITIVE: 1,
            NewsSentiment.NEUTRAL: 0,
            NewsSentiment.NEGATIVE: -1,
        }[signal.sentiment]
        score += direction * signal.confidence * signal.importance
    return score


def _buy_confirmed(
    model_side: SignalSide | None,
    quantitative: QuantitativeContext,
    regime: RegimeClassification,
    news_score: float,
) -> bool:
    return (
        model_side is SignalSide.BUY
        and quantitative.trend > 0
        and quantitative.momentum > 0
        and regime.market_regime is MarketRegime.BULL
        and regime.volatility_regime is VolatilityRegime.LOW
        and news_score >= 0
    )


def _sell_confirmed(
    model_side: SignalSide | None,
    quantitative: QuantitativeContext,
    regime: RegimeClassification,
    news_score: float,
    news_score_threshold: float,
) -> bool:
    return (
        model_side is SignalSide.SELL
        or (quantitative.trend < 0 and quantitative.momentum < 0)
        or regime.market_regime is MarketRegime.BEAR
        or regime.volatility_regime is VolatilityRegime.HIGH
        or news_score <= -news_score_threshold
    )
