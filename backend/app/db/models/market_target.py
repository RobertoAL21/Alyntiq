from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MarketTarget(Base):
    """A versioned supervised-learning target for one provenance-qualified bar."""

    __tablename__ = "market_targets"
    __table_args__ = (
        UniqueConstraint(
            "symbol",
            "timestamp",
            "source",
            "timeframe",
            "target_version",
            name="uq_market_targets_identity",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(8), nullable=False)
    target_version: Mapped[str] = mapped_column(String(32), nullable=False)
    direction_1d: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
