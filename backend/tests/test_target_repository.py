from conftest import make_feature_bars
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.market_target import MarketTarget
from app.targets.generator import TargetGenerator
from app.targets.repository import INSERT_BATCH_SIZE, store_market_targets


def test_storage_is_idempotent_per_target_version(db_session: Session) -> None:
    targets = TargetGenerator().generate(make_feature_bars(periods=2))

    first_result = store_market_targets(db_session, targets, target_version="targets-v1")
    db_session.commit()
    second_result = store_market_targets(db_session, targets, target_version="targets-v1")
    db_session.commit()
    versioned_result = store_market_targets(db_session, targets, target_version="targets-v2")
    db_session.commit()

    stored_count = db_session.scalar(select(func.count()).select_from(MarketTarget))

    assert first_result.inserted == 6
    assert second_result.inserted == 0
    assert second_result.skipped == 6
    assert versioned_result.inserted == 6
    assert stored_count == 12


def test_storage_batches_large_target_datasets(db_session: Session) -> None:
    targets = TargetGenerator().generate(make_feature_bars(periods=(INSERT_BATCH_SIZE // 3) + 1))

    result = store_market_targets(db_session, targets, target_version="targets-v1")
    db_session.commit()

    assert result.inserted == len(targets)
