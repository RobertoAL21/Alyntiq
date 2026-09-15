"""create trading decisions

Revision ID: 20260915_0005
Revises: 20260911_0004
Create Date: 2026-09-15 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260915_0005"
down_revision: str | None = "20260911_0004"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "trading_decisions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("model_version", sa.String(length=64)),
        sa.Column("strategy_version", sa.String(length=64)),
        sa.Column("feature_version", sa.String(length=64)),
        sa.Column("prediction", sa.Numeric(precision=20, scale=10)),
        sa.Column("confidence", sa.Numeric(precision=20, scale=10)),
        sa.Column("signal", sa.String(length=16), nullable=False),
        sa.Column("risk_decision", sa.String(length=16), nullable=False),
        sa.Column("order_id", sa.String(length=64)),
        sa.Column("executed", sa.Boolean(), nullable=False),
        sa.Column("price", sa.Numeric(precision=20, scale=8)),
        sa.Column("quantity", sa.Integer()),
        sa.Column("reason", sa.String(length=512), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("signal IN ('buy', 'sell', 'hold')", name="ck_trading_decisions_signal"),
        sa.CheckConstraint(
            "risk_decision IN ('approved', 'rejected', 'not_evaluated')",
            name="ck_trading_decisions_risk_decision",
        ),
        sa.CheckConstraint(
            "quantity IS NULL OR quantity > 0",
            name="ck_trading_decisions_quantity_positive",
        ),
        sa.CheckConstraint(
            "price IS NULL OR price > 0", name="ck_trading_decisions_price_positive"
        ),
        sa.CheckConstraint(
            "executed = false OR (order_id IS NOT NULL AND price IS NOT NULL "
            "AND quantity IS NOT NULL)",
            name="ck_trading_decisions_execution_details",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id", name="uq_trading_decisions_order_id"),
    )
    op.create_index(
        "ix_trading_decisions_symbol_timestamp",
        "trading_decisions",
        ["symbol", "timestamp"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_trading_decisions_symbol_timestamp", table_name="trading_decisions")
    op.drop_table("trading_decisions")
