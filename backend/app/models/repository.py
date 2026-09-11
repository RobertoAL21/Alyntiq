import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.market_feature import MarketFeature
from app.db.models.market_target import MarketTarget
from app.features.constants import FEATURE_COLUMNS
from app.models.dataset import DatasetMetadata, TrainingDataset


class TrainingDatasetError(ValueError):
    """Raised when selected feature and target versions cannot form a training dataset."""


def load_training_dataset(
    session: Session,
    *,
    source: str,
    timeframe: str,
    feature_version: str,
    target_version: str,
    dataset_version: str,
) -> TrainingDataset:
    """Join versioned features and labels only for supervised-training evaluation."""
    target_identity = (
        (MarketFeature.symbol == MarketTarget.symbol)
        & (MarketFeature.timestamp == MarketTarget.timestamp)
        & (MarketFeature.source == MarketTarget.source)
        & (MarketFeature.timeframe == MarketTarget.timeframe)
    )
    statement = (
        select(
            MarketFeature.timestamp,
            MarketFeature.symbol,
            *[getattr(MarketFeature, column) for column in FEATURE_COLUMNS],
            MarketTarget.direction_1d,
        )
        .join(MarketTarget, target_identity)
        .where(
            MarketFeature.source == source,
            MarketFeature.timeframe == timeframe,
            MarketFeature.feature_version == feature_version,
            MarketTarget.target_version == target_version,
            MarketTarget.direction_1d.is_not(None),
        )
        .order_by(MarketFeature.timestamp, MarketFeature.symbol)
    )
    frame = pd.read_sql(statement, session.connection())
    frame = frame.dropna(subset=FEATURE_COLUMNS).reset_index(drop=True)
    if frame.empty:
        raise TrainingDatasetError("no complete feature rows with non-null targets were found")

    metadata = DatasetMetadata(
        dataset_version=dataset_version,
        feature_version=feature_version,
        target_version=target_version,
        source=source,
        timeframe=timeframe,
    )
    return TrainingDataset(
        features=frame.loc[:, FEATURE_COLUMNS].astype(float),
        target=frame["direction_1d"].astype(bool),
        timestamps=pd.to_datetime(frame["timestamp"], utc=True),
        metadata=metadata,
    )
