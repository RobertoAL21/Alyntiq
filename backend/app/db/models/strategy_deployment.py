from datetime import datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, Index, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StrategyDeploymentRecord(Base):
    """Persisted configuration that may be armed for a future paper-trading worker."""

    __tablename__ = "strategy_deployments"
    __table_args__ = (
        CheckConstraint(
            "state IN ('draft', 'validated', 'armed')",
            name="ck_strategy_deployments_state",
        ),
        Index("ix_strategy_deployments_state", "state"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(96), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    feature_version: Mapped[str] = mapped_column(String(64), nullable=False)
    target_version: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(8), nullable=False)
    symbols: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    buy_threshold: Mapped[object] = mapped_column(Numeric(20, 10), nullable=False)
    sell_threshold: Mapped[object] = mapped_column(Numeric(20, 10), nullable=False)
    order_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_limits: Mapped[dict[str, str | int]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
