from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TradingDecisionRecord(Base):
    """Persisted, append-first audit state for one trade proposal and its execution outcome."""

    __tablename__ = "trading_decisions"
    __table_args__ = (
        CheckConstraint("signal IN ('buy', 'sell', 'hold')", name="ck_trading_decisions_signal"),
        CheckConstraint(
            "risk_decision IN ('approved', 'rejected', 'not_evaluated')",
            name="ck_trading_decisions_risk_decision",
        ),
        CheckConstraint(
            "quantity IS NULL OR quantity > 0",
            name="ck_trading_decisions_quantity_positive",
        ),
        CheckConstraint("price IS NULL OR price > 0", name="ck_trading_decisions_price_positive"),
        CheckConstraint(
            "executed = false OR (order_id IS NOT NULL AND price IS NOT NULL "
            "AND quantity IS NOT NULL)",
            name="ck_trading_decisions_execution_details",
        ),
        UniqueConstraint("order_id", name="uq_trading_decisions_order_id"),
        Index("ix_trading_decisions_symbol_timestamp", "symbol", "timestamp"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(64))
    strategy_version: Mapped[str | None] = mapped_column(String(64))
    feature_version: Mapped[str | None] = mapped_column(String(64))
    prediction: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    signal: Mapped[str] = mapped_column(String(16), nullable=False)
    risk_decision: Mapped[str] = mapped_column(String(16), nullable=False)
    order_id: Mapped[str | None] = mapped_column(String(64))
    executed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    price: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    quantity: Mapped[int | None] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
