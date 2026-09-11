from conftest import make_feature_bars
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.market_feature import MarketFeature
from app.features.calculator import calculate_features
from app.features.repository import INSERT_BATCH_SIZE, store_market_features


def test_storage_is_idempotent_per_feature_version(db_session: Session) -> None:
    features = calculate_features(make_feature_bars(periods=2))

    first_result = store_market_features(db_session, features, feature_version="features-v1")
    db_session.commit()
    second_result = store_market_features(db_session, features, feature_version="features-v1")
    db_session.commit()
    versioned_result = store_market_features(db_session, features, feature_version="features-v2")
    db_session.commit()

    stored_count = db_session.scalar(select(func.count()).select_from(MarketFeature))

    assert first_result.inserted == 6
    assert second_result.inserted == 0
    assert second_result.skipped == 6
    assert versioned_result.inserted == 6
    assert stored_count == 12


def test_storage_batches_large_feature_datasets(db_session: Session) -> None:
    features = calculate_features(make_feature_bars(periods=(INSERT_BATCH_SIZE // 3) + 1))

    result = store_market_features(db_session, features, feature_version="features-v1")
    db_session.commit()

    assert result.inserted == len(features)
