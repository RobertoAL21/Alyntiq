from conftest import make_bar
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.market_bar import MarketBar
from app.market_data.repository import store_historical_bars


def test_storage_is_idempotent(db_session: Session) -> None:
    bar = make_bar()

    first_result = store_historical_bars(db_session, [bar])
    db_session.commit()
    second_result = store_historical_bars(db_session, [bar])
    db_session.commit()

    stored_count = db_session.scalar(select(func.count()).select_from(MarketBar))

    assert first_result.inserted == 1
    assert second_result.inserted == 0
    assert second_result.skipped == 1
    assert stored_count == 1
