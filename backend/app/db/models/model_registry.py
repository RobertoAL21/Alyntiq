from datetime import datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ModelRegistryRecord(Base):
    """Persisted provenance and lifecycle state for a reproducible model version."""

    __tablename__ = "model_registry"
    __table_args__ = (
        CheckConstraint(
            "state IN ('candidate', 'staging', 'production', 'retired')",
            name="ck_model_registry_state",
        ),
        UniqueConstraint("model_version", name="uq_model_registry_model_version"),
        Index("ix_model_registry_state", "state"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    model_family: Mapped[str] = mapped_column(String(32), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    dataset_version: Mapped[str] = mapped_column(String(64), nullable=False)
    feature_version: Mapped[str] = mapped_column(String(64), nullable=False)
    target_version: Mapped[str] = mapped_column(String(64), nullable=False)
    parameters: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    metrics: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    backtest_results: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    artifact_uri: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
