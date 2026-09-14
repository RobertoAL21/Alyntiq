from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from math import isfinite

from app.backtesting.types import (
    BacktestBar,
    Portfolio,
    Signal,
    SignalLineage,
    SignalSide,
)

DEFAULT_SELL_THRESHOLDS = (0.25, 0.30, 0.35, 0.40, 0.45)
DEFAULT_BUY_THRESHOLDS = (0.55, 0.60, 0.65, 0.70, 0.75)


class MLStrategyError(ValueError):
    """Raised when versioned model predictions cannot produce a safe strategy proposal."""


@dataclass(frozen=True)
class ModelPrediction:
    """One point-in-time probability supplied by a model-inference process."""

    timestamp: datetime
    symbol: str
    up_probability: float
    model_version: str
    feature_version: str

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise MLStrategyError("prediction timestamps must include a timezone")
        if not self.symbol.strip():
            raise MLStrategyError("prediction symbol must not be blank")
        if not isfinite(self.up_probability) or not 0 <= self.up_probability <= 1:
            raise MLStrategyError("up_probability must be a finite value between 0 and 1")
        if not self.model_version.strip():
            raise MLStrategyError("model_version must not be blank")
        if not self.feature_version.strip():
            raise MLStrategyError("feature_version must not be blank")
        object.__setattr__(self, "timestamp", self.timestamp.astimezone(UTC))
        object.__setattr__(self, "symbol", self.symbol.strip().upper())


@dataclass(frozen=True)
class ValidationPrediction:
    """A labeled prediction used only for validation-time threshold selection."""

    prediction: ModelPrediction
    target_direction: bool


@dataclass(frozen=True)
class MLStrategyParameters:
    quantity: int
    strategy_version: str = "ml-threshold-v1"

    def __post_init__(self) -> None:
        if self.quantity < 1:
            raise MLStrategyError("quantity must be at least 1")
        if not self.strategy_version.strip():
            raise MLStrategyError("strategy_version must not be blank")


@dataclass(frozen=True)
class ThresholdSelection:
    sell_threshold: float
    buy_threshold: float
    validation_directional_accuracy: float
    validation_observations: int
    validation_action_count: int


def select_thresholds(
    validation_predictions: Sequence[ValidationPrediction],
    *,
    sell_candidates: Sequence[float] = DEFAULT_SELL_THRESHOLDS,
    buy_candidates: Sequence[float] = DEFAULT_BUY_THRESHOLDS,
) -> ThresholdSelection:
    """Select thresholds solely from labeled validation predictions, never holdout data."""
    if not validation_predictions:
        raise MLStrategyError("at least one validation prediction is required")
    _validate_candidates(sell_candidates, buy_candidates)
    candidates = []
    for sell_threshold in sell_candidates:
        for buy_threshold in buy_candidates:
            correct = 0
            action_count = 0
            for validation_prediction in validation_predictions:
                side = _classify_probability(
                    validation_prediction.prediction.up_probability,
                    sell_threshold=sell_threshold,
                    buy_threshold=buy_threshold,
                )
                if side is None:
                    continue
                action_count += 1
                if (side is SignalSide.BUY) == validation_prediction.target_direction:
                    correct += 1
            candidates.append(
                (
                    correct / len(validation_predictions),
                    action_count,
                    sell_threshold,
                    buy_threshold,
                )
            )
    score, action_count, sell_threshold, buy_threshold = max(candidates)
    return ThresholdSelection(
        sell_threshold=sell_threshold,
        buy_threshold=buy_threshold,
        validation_directional_accuracy=score,
        validation_observations=len(validation_predictions),
        validation_action_count=action_count,
    )


@dataclass
class MLThresholdStrategy:
    """Convert supplied model probabilities into long-only threshold signals for the engine."""

    predictions: Mapping[datetime, ModelPrediction]
    parameters: MLStrategyParameters
    thresholds: ThresholdSelection

    def on_bar(self, bar: BacktestBar, portfolio: Portfolio) -> Signal | None:
        prediction = self.predictions.get(bar.timestamp)
        if prediction is None:
            return None
        if prediction.symbol != bar.symbol:
            raise MLStrategyError("prediction symbol must match the backtest bar symbol")
        side = _classify_probability(
            prediction.up_probability,
            sell_threshold=self.thresholds.sell_threshold,
            buy_threshold=self.thresholds.buy_threshold,
        )
        lineage = SignalLineage(
            model_version=prediction.model_version,
            strategy_version=self.parameters.strategy_version,
            feature_version=prediction.feature_version,
            up_probability=prediction.up_probability,
        )
        if side is SignalSide.BUY and portfolio.position is None:
            return Signal(bar.timestamp, bar.symbol, side, self.parameters.quantity, lineage)
        if side is SignalSide.SELL and portfolio.position is not None:
            return Signal(bar.timestamp, bar.symbol, side, portfolio.position.quantity, lineage)
        return None


def _classify_probability(
    probability: float,
    *,
    sell_threshold: float,
    buy_threshold: float,
) -> SignalSide | None:
    if probability <= sell_threshold:
        return SignalSide.SELL
    if probability >= buy_threshold:
        return SignalSide.BUY
    return None


def _validate_candidates(sell_candidates: Sequence[float], buy_candidates: Sequence[float]) -> None:
    if not sell_candidates or not buy_candidates:
        raise MLStrategyError("sell and buy threshold candidates must not be empty")
    for threshold in (*sell_candidates, *buy_candidates):
        if not isfinite(threshold) or not 0 <= threshold <= 1:
            raise MLStrategyError("threshold candidates must be finite values between 0 and 1")
    if any(sell >= buy for sell in sell_candidates for buy in buy_candidates):
        raise MLStrategyError(
            "every sell threshold candidate must be below every buy threshold candidate"
        )
