from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MarketBar(Base):
    """A validated historical OHLCV bar from a named market-data source."""

    __tablename__ = "market_bars"
    __table_args__ = (
        CheckConstraint("open > 0", name="ck_market_bars_open_positive"),
        CheckConstraint("high > 0", name="ck_market_bars_high_positive"),
        CheckConstraint("low > 0", name="ck_market_bars_low_positive"),
        CheckConstraint("close > 0", name="ck_market_bars_close_positive"),
        CheckConstraint("volume >= 0", name="ck_market_bars_volume_nonnegative"),
        UniqueConstraint(
            "symbol",
            "timestamp",
            "timeframe",
            "source",
            name="uq_market_bars_identity",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(8), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
