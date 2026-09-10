"""create market bars

Revision ID: 20260910_0002
Revises: 20260909_0001
Create Date: 2026-09-10 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260910_0002"
down_revision: str | None = "20260909_0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "market_bars",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("high", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("low", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("close", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("timeframe", sa.String(length=8), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("open > 0", name="ck_market_bars_open_positive"),
        sa.CheckConstraint("high > 0", name="ck_market_bars_high_positive"),
        sa.CheckConstraint("low > 0", name="ck_market_bars_low_positive"),
        sa.CheckConstraint("close > 0", name="ck_market_bars_close_positive"),
        sa.CheckConstraint("volume >= 0", name="ck_market_bars_volume_nonnegative"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "symbol",
            "timestamp",
            "timeframe",
            "source",
            name="uq_market_bars_identity",
        ),
    )


def downgrade() -> None:
    op.drop_table("market_bars")
