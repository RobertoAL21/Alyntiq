"""create market targets

Revision ID: 20260911_0004
Revises: 20260910_0003
Create Date: 2026-09-11 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260911_0004"
down_revision: str | None = "20260910_0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "market_targets",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("timeframe", sa.String(length=8), nullable=False),
        sa.Column("target_version", sa.String(length=32), nullable=False),
        sa.Column("direction_1d", sa.Boolean()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "symbol",
            "timestamp",
            "source",
            "timeframe",
            "target_version",
            name="uq_market_targets_identity",
        ),
    )


def downgrade() -> None:
    op.drop_table("market_targets")
