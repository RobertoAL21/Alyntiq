from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.backtesting.engine import BacktestEngine
from app.backtesting.types import BacktestBar, BacktestConfig, SignalSide
from app.strategies.ml import (
    MLStrategyError,
    MLStrategyParameters,
    MLThresholdStrategy,
    ModelPrediction,
    ThresholdSelection,
    ValidationPrediction,
    select_thresholds,
)


def make_bar(index: int, price: str) -> BacktestBar:
    value = Decimal(price)
    return BacktestBar(
        timestamp=datetime(2024, 1, 2, tzinfo=UTC) + timedelta(days=index),
        symbol="AAPL",
        open=value,
        high=value + Decimal("1"),
        low=value - Decimal("1"),
        close=value,
    )


def make_prediction(timestamp: datetime, probability: float) -> ModelPrediction:
    return ModelPrediction(
        timestamp=timestamp,
        symbol="AAPL",
        up_probability=probability,
        model_version="advanced-v1",
        feature_version="features-v1",
    )


def test_selects_thresholds_using_only_labeled_validation_predictions() -> None:
    timestamp = datetime(2024, 1, 2, tzinfo=UTC)
    validation_predictions = (
        ValidationPrediction(make_prediction(timestamp, 0.9), True),
        ValidationPrediction(make_prediction(timestamp + timedelta(days=1), 0.7), True),
        ValidationPrediction(make_prediction(timestamp + timedelta(days=2), 0.5), False),
        ValidationPrediction(make_prediction(timestamp + timedelta(days=3), 0.3), False),
        ValidationPrediction(make_prediction(timestamp + timedelta(days=4), 0.1), False),
    )

    selection = select_thresholds(
        validation_predictions,
        sell_candidates=(0.2, 0.4),
        buy_candidates=(0.6, 0.8),
    )

    assert selection.sell_threshold == 0.4
    assert selection.buy_threshold == 0.6
    assert selection.validation_directional_accuracy == 0.8
    assert selection.validation_observations == 5
    assert selection.validation_action_count == 4


def test_ml_strategy_creates_versioned_signals_and_propagates_lineage_to_trade() -> None:
    bars = (
        make_bar(0, "100"),
        make_bar(1, "101"),
        make_bar(2, "110"),
        make_bar(3, "111"),
    )
    strategy = MLThresholdStrategy(
        predictions={
            bars[0].timestamp: make_prediction(bars[0].timestamp, 0.8),
            bars[1].timestamp: make_prediction(bars[1].timestamp, 0.5),
            bars[2].timestamp: make_prediction(bars[2].timestamp, 0.2),
        },
        parameters=MLStrategyParameters(quantity=2, strategy_version="ml-threshold-v1"),
        thresholds=ThresholdSelection(0.3, 0.7, 0.75, 20, 15),
    )

    result = BacktestEngine(BacktestConfig(initial_cash=Decimal("1000"))).run(bars, strategy)

    assert [fill.side for fill in result.fills] == [SignalSide.BUY, SignalSide.SELL]
    trade = result.trades[0]
    assert trade.entry_lineage is not None
    assert trade.exit_lineage is not None
    assert trade.entry_lineage.model_version == "advanced-v1"
    assert trade.entry_lineage.feature_version == "features-v1"
    assert trade.entry_lineage.strategy_version == "ml-threshold-v1"
    assert trade.entry_lineage.up_probability == 0.8
    assert trade.exit_lineage.up_probability == 0.2


def test_ml_strategy_holds_without_a_prediction_and_rejects_symbol_mismatch() -> None:
    bar = make_bar(0, "100")
    strategy = MLThresholdStrategy(
        predictions={},
        parameters=MLStrategyParameters(quantity=1),
        thresholds=ThresholdSelection(0.3, 0.7, 0.0, 1, 0),
    )

    assert BacktestEngine().run((bar,), strategy).orders == ()

    mismatched = ModelPrediction(
        timestamp=bar.timestamp,
        symbol="MSFT",
        up_probability=0.8,
        model_version="advanced-v1",
        feature_version="features-v1",
    )
    strategy = MLThresholdStrategy(
        predictions={bar.timestamp: mismatched},
        parameters=MLStrategyParameters(quantity=1),
        thresholds=ThresholdSelection(0.3, 0.7, 0.0, 1, 0),
    )

    with pytest.raises(MLStrategyError, match="symbol"):
        BacktestEngine().run((bar,), strategy)
