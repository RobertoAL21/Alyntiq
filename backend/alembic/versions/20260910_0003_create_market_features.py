"""create market features

Revision ID: 20260910_0003
Revises: 20260910_0002
Create Date: 2026-09-10 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260910_0003"
down_revision: str | None = "20260910_0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "market_features",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("timeframe", sa.String(length=8), nullable=False),
        sa.Column("feature_version", sa.String(length=32), nullable=False),
        sa.Column("returns_1d", sa.Numeric(precision=20, scale=10)),
        sa.Column("returns_5d", sa.Numeric(precision=20, scale=10)),
        sa.Column("returns_10d", sa.Numeric(precision=20, scale=10)),
        sa.Column("returns_20d", sa.Numeric(precision=20, scale=10)),
        sa.Column("momentum_5", sa.Numeric(precision=20, scale=10)),
        sa.Column("momentum_10", sa.Numeric(precision=20, scale=10)),
        sa.Column("momentum_20", sa.Numeric(precision=20, scale=10)),
        sa.Column("sma_10", sa.Numeric(precision=20, scale=8)),
        sa.Column("sma_20", sa.Numeric(precision=20, scale=8)),
        sa.Column("sma_50", sa.Numeric(precision=20, scale=8)),
        sa.Column("ema_10", sa.Numeric(precision=20, scale=8)),
        sa.Column("ema_20", sa.Numeric(precision=20, scale=8)),
        sa.Column("volatility_10", sa.Numeric(precision=20, scale=10)),
        sa.Column("volatility_20", sa.Numeric(precision=20, scale=10)),
        sa.Column("atr_14", sa.Numeric(precision=20, scale=8)),
        sa.Column("rsi_14", sa.Numeric(precision=20, scale=8)),
        sa.Column("macd", sa.Numeric(precision=20, scale=8)),
        sa.Column("macd_signal", sa.Numeric(precision=20, scale=8)),
        sa.Column("bollinger_upper", sa.Numeric(precision=20, scale=8)),
        sa.Column("bollinger_lower", sa.Numeric(precision=20, scale=8)),
        sa.Column("volume_change", sa.Numeric(precision=20, scale=10)),
        sa.Column("volume_ma_20", sa.Numeric(precision=20, scale=8)),
        sa.Column("volume_ratio", sa.Numeric(precision=20, scale=10)),
        sa.Column("spy_returns_1d", sa.Numeric(precision=20, scale=10)),
        sa.Column("qqq_returns_1d", sa.Numeric(precision=20, scale=10)),
        sa.Column("spy_volatility_20", sa.Numeric(precision=20, scale=10)),
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
            "feature_version",
            name="uq_market_features_identity",
        ),
    )


def downgrade() -> None:
    op.drop_table("market_features")
