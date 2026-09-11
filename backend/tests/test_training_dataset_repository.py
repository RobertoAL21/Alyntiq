from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.db.models.market_feature import MarketFeature
from app.db.models.market_target import MarketTarget
from app.features.constants import FEATURE_COLUMNS
from app.models.repository import load_training_dataset


def seed_training_rows(db_session: Session, periods: int = 8) -> None:
    start = datetime(2024, 1, 2, tzinfo=UTC)
    for index in range(periods):
        timestamp = start + timedelta(days=index)
        db_session.add(
            MarketFeature(
                symbol="AAPL",
                timestamp=timestamp,
                source="alpaca:iex:raw",
                timeframe="1D",
                feature_version="features-v1",
                **{column: float(index + 1) for column in FEATURE_COLUMNS},
            )
        )
        db_session.add(
            MarketTarget(
                symbol="AAPL",
                timestamp=timestamp,
                source="alpaca:iex:raw",
                timeframe="1D",
                target_version="targets-v1",
                direction_1d=None if index == periods - 1 else bool(index % 2),
            )
        )
    db_session.commit()


def test_loads_complete_versioned_features_and_keeps_targets_separate(db_session: Session) -> None:
    seed_training_rows(db_session)

    dataset = load_training_dataset(
        db_session,
        source="alpaca:iex:raw",
        timeframe="1D",
        feature_version="features-v1",
        target_version="targets-v1",
        dataset_version="dataset-v1",
    )

    assert dataset.row_count == 7
    assert list(dataset.features.columns) == list(FEATURE_COLUMNS)
    assert "direction_1d" not in dataset.features.columns
    assert dataset.target.tolist() == [False, True, False, True, False, True, False]
    assert dataset.metadata.feature_version == "features-v1"
    assert dataset.metadata.target_version == "targets-v1"
