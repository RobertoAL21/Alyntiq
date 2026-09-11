import pytest
from sqlalchemy.orm import Session

from app.targets.service import TargetBuildError, TargetGenerationService


def test_build_rejects_an_empty_market_data_selection(db_session: Session) -> None:
    with pytest.raises(TargetBuildError, match="no market bars"):
        TargetGenerationService().build(
            db_session,
            source="alpaca:iex:raw",
            timeframe="1D",
        )
