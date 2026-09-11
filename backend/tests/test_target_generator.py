import pandas as pd
import pytest

from app.db.models.market_feature import MarketFeature
from app.db.models.market_target import MarketTarget
from app.features.constants import FEATURE_COLUMNS
from app.targets.constants import TARGET_COLUMNS, TARGET_IDENTITY_COLUMNS
from app.targets.generator import TargetCalculationError, TargetGenerator


def make_target_bars() -> pd.DataFrame:
    timestamps = pd.date_range("2024-01-02", periods=4, freq="B", tz="UTC")
    return pd.DataFrame(
        [
            {
                "symbol": "AAPL",
                "timestamp": timestamp,
                "close": close,
                "source": "alpaca:iex:raw",
                "timeframe": "1D",
            }
            for timestamp, close in zip(timestamps, (100.0, 99.0, 99.0, 102.0), strict=True)
        ]
    )


def test_generates_next_day_direction_and_retains_the_unknown_final_label() -> None:
    targets = TargetGenerator().generate(make_target_bars())

    assert list(targets.columns) == [*TARGET_IDENTITY_COLUMNS, *TARGET_COLUMNS]
    assert targets["direction_1d"].tolist()[:3] == [False, False, True]
    assert pd.isna(targets.loc[3, "direction_1d"])


def test_separates_targets_from_inference_features() -> None:
    target_columns = set(TARGET_COLUMNS)

    assert target_columns.isdisjoint(FEATURE_COLUMNS)
    assert target_columns.isdisjoint(MarketFeature.__table__.columns.keys())
    assert MarketTarget.__tablename__ != MarketFeature.__tablename__


def test_rejects_bars_without_closing_prices() -> None:
    bars = make_target_bars().drop(columns="close")

    with pytest.raises(TargetCalculationError, match="close"):
        TargetGenerator().generate(bars)
