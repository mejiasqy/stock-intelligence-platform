"""create_indicator_snapshots

Revision ID: d1e2f3a4b5c6
Revises: a1b2c3d4e5f6
Create Date: 2026-06-23 22:05:00.000000

Um snapshot por (asset_id, timeframe, source) — upsert substitui o anterior.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d1e2f3a4b5c6"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "indicator_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("timeframe", sa.String(10), nullable=False, server_default="1d"),
        sa.Column("source", sa.String(50), nullable=False, server_default="yfinance"),
        sa.Column(
            "calculated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("calculation_version", sa.String(20), nullable=False),
        sa.Column("candles_used", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        # Returns
        sa.Column("return_1d", sa.Numeric(10, 6), nullable=True),
        sa.Column("return_5d", sa.Numeric(10, 6), nullable=True),
        sa.Column("return_20d", sa.Numeric(10, 6), nullable=True),
        sa.Column("return_60d", sa.Numeric(10, 6), nullable=True),
        # Moving averages
        sa.Column("sma_20", sa.Numeric(18, 6), nullable=True),
        sa.Column("sma_50", sa.Numeric(18, 6), nullable=True),
        sa.Column("ema_20", sa.Numeric(18, 6), nullable=True),
        # Oscillators
        sa.Column("rsi_14", sa.Numeric(8, 4), nullable=True),
        sa.Column("macd", sa.Numeric(18, 6), nullable=True),
        sa.Column("macd_signal", sa.Numeric(18, 6), nullable=True),
        sa.Column("macd_histogram", sa.Numeric(18, 6), nullable=True),
        # Bollinger Bands
        sa.Column("bollinger_upper", sa.Numeric(18, 6), nullable=True),
        sa.Column("bollinger_middle", sa.Numeric(18, 6), nullable=True),
        sa.Column("bollinger_lower", sa.Numeric(18, 6), nullable=True),
        # Volume
        sa.Column("volume_avg_20", sa.Numeric(20, 2), nullable=True),
        # Risk
        sa.Column("vol_annualized_20d", sa.Numeric(10, 6), nullable=True),
        sa.Column("max_drawdown_60d", sa.Numeric(10, 6), nullable=True),
        sa.Column("current_drawdown_60d", sa.Numeric(10, 6), nullable=True),
        # Missing fields metadata
        sa.Column("insufficient_fields", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_id", "timeframe", "source", name="uq_snapshot_asset_tf_src"),
    )
    op.create_index(op.f("ix_indicator_snapshots_id"), "indicator_snapshots", ["id"], unique=False)
    op.create_index(
        op.f("ix_indicator_snapshots_asset_id"), "indicator_snapshots", ["asset_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_indicator_snapshots_asset_id"), table_name="indicator_snapshots")
    op.drop_index(op.f("ix_indicator_snapshots_id"), table_name="indicator_snapshots")
    op.drop_table("indicator_snapshots")
