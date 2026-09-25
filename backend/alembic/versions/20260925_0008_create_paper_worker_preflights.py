"""create paper worker preflights

Revision ID: 20260925_0008
Revises: 20260924_0007
Create Date: 2026-09-25 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260925_0008"
down_revision: str | None = "20260924_0007"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "paper_worker_preflights",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("deployment_id", sa.String(length=36), nullable=False),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column("reason", sa.String(length=512), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "outcome IN ('ready', 'blocked')", name="ck_paper_worker_preflights_outcome"
        ),
        sa.ForeignKeyConstraint(["deployment_id"], ["strategy_deployments.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_paper_worker_preflights_deployment_checked_at",
        "paper_worker_preflights",
        ["deployment_id", "checked_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_paper_worker_preflights_deployment_checked_at",
        table_name="paper_worker_preflights",
    )
    op.drop_table("paper_worker_preflights")
