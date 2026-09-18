"""create model registry

Revision ID: 20260917_0006
Revises: 20260915_0005
Create Date: 2026-09-17 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260917_0006"
down_revision: str | None = "20260915_0005"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "model_registry",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("model_name", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("model_family", sa.String(length=32), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("dataset_version", sa.String(length=64), nullable=False),
        sa.Column("feature_version", sa.String(length=64), nullable=False),
        sa.Column("target_version", sa.String(length=64), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("backtest_results", sa.JSON(), nullable=False),
        sa.Column("artifact_uri", sa.String(length=512), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "state IN ('candidate', 'staging', 'production', 'retired')",
            name="ck_model_registry_state",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("model_version", name="uq_model_registry_model_version"),
    )
    op.create_index("ix_model_registry_state", "model_registry", ["state"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_model_registry_state", table_name="model_registry")
    op.drop_table("model_registry")
