from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MarketFeature(Base):
    """A point-in-time, versioned feature row derived from one market bar."""

    __tablename__ = "market_features"
    __table_args__ = (
        UniqueConstraint(
            "symbol",
            "timestamp",
            "source",
            "timeframe",
            "feature_version",
            name="uq_market_features_identity",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(8), nullable=False)
    feature_version: Mapped[str] = mapped_column(String(32), nullable=False)
    returns_1d: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    returns_5d: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    returns_10d: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    returns_20d: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    momentum_5: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    momentum_10: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    momentum_20: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    sma_10: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    sma_20: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    sma_50: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    ema_10: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    ema_20: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    volatility_10: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    volatility_20: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    atr_14: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    rsi_14: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    macd: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    macd_signal: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    bollinger_upper: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    bollinger_lower: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    volume_change: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    volume_ma_20: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    volume_ratio: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    spy_returns_1d: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    qqq_returns_1d: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    spy_volatility_20: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
