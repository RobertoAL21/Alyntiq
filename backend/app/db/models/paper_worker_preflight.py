from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PaperWorkerPreflightRecord(Base):
    """Immutable one-cycle eligibility result; it does not represent execution."""

    __tablename__ = "paper_worker_preflights"
    __table_args__ = (
        CheckConstraint(
            "outcome IN ('ready', 'blocked')", name="ck_paper_worker_preflights_outcome"
        ),
        Index(
            "ix_paper_worker_preflights_deployment_checked_at",
            "deployment_id",
            "checked_at",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    deployment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("strategy_deployments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    reason: Mapped[str] = mapped_column(String(512), nullable=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
