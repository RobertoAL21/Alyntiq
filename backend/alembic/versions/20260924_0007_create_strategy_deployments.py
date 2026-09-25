"""create paper strategy deployments

Revision ID: 20260924_0007
Revises: 20260917_0006
Create Date: 2026-09-24 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260924_0007"
down_revision: str | None = "20260917_0006"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "strategy_deployments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=96), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("strategy_version", sa.String(length=64), nullable=False),
        sa.Column("feature_version", sa.String(length=64), nullable=False),
        sa.Column("target_version", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("timeframe", sa.String(length=8), nullable=False),
        sa.Column("symbols", sa.JSON(), nullable=False),
        sa.Column("buy_threshold", sa.Numeric(precision=20, scale=10), nullable=False),
        sa.Column("sell_threshold", sa.Numeric(precision=20, scale=10), nullable=False),
        sa.Column("order_quantity", sa.Integer(), nullable=False),
        sa.Column("risk_limits", sa.JSON(), nullable=False),
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
            "state IN ('draft', 'validated', 'armed')",
            name="ck_strategy_deployments_state",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_strategy_deployments_state", "strategy_deployments", ["state"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_strategy_deployments_state", table_name="strategy_deployments")
    op.drop_table("strategy_deployments")
