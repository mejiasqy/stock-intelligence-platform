"""add_timeframe_source_to_price_bars

Revision ID: a1b2c3d4e5f6
Revises: 0fa13a0047fc
Create Date: 2026-06-23 22:00:00.000000

Adds `timeframe` and `source` to price_bars, replaces the old UNIQUE(asset_id, timestamp)
constraint with UNIQUE(asset_id, timeframe, timestamp, source), and adds a composite index
optimised for indicator queries.

Downgrade safety: the rollback verifies that no two rows share (asset_id, timestamp) across
different timeframe/source values before recreating the old constraint.  If collisions exist
the downgrade aborts to avoid silent data loss.  The downgrade is only safe while all data
remains compatible with the original single-timeframe / single-source assumption.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "0fa13a0047fc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add columns — NOT NULL DEFAULT lets PostgreSQL backfill existing rows instantly.
    op.add_column(
        "price_bars",
        sa.Column("timeframe", sa.String(10), nullable=False, server_default="1d"),
    )
    op.add_column(
        "price_bars",
        sa.Column("source", sa.String(50), nullable=False, server_default="yfinance"),
    )

    # 2. Remove the old unique constraint.
    op.drop_constraint("uq_price_bar_asset_ts", "price_bars", type_="unique")

    # 3. Create the new unique constraint covering timeframe and source.
    op.create_unique_constraint(
        "uq_price_bar_asset_timeframe_ts_source",
        "price_bars",
        ["asset_id", "timeframe", "timestamp", "source"],
    )

    # 4. Composite index for indicator queries: latest N candles of a given asset/timeframe.
    op.create_index(
        "ix_price_bars_asset_timeframe_ts",
        "price_bars",
        ["asset_id", "timeframe", sa.text("timestamp DESC")],
    )


def downgrade() -> None:
    conn = op.get_bind()

    # Verify that no (asset_id, timestamp) pair exists across multiple timeframe/source values.
    # If it does, the old constraint cannot be safely recreated.
    result = conn.execute(
        sa.text(
            "SELECT COUNT(*) FROM ("
            "  SELECT asset_id, timestamp"
            "  FROM price_bars"
            "  GROUP BY asset_id, timestamp"
            "  HAVING COUNT(*) > 1"
            ") AS collisions"
        )
    )
    collision_count: int = result.scalar() or 0
    if collision_count > 0:
        raise RuntimeError(
            f"Downgrade aborted: {collision_count} (asset_id, timestamp) collision(s) found. "
            "The original UNIQUE(asset_id, timestamp) constraint cannot be safely recreated. "
            "Remove duplicate timeframe/source rows before downgrading."
        )

    op.drop_index("ix_price_bars_asset_timeframe_ts", table_name="price_bars")
    op.drop_constraint("uq_price_bar_asset_timeframe_ts_source", "price_bars", type_="unique")
    op.drop_column("price_bars", "source")
    op.drop_column("price_bars", "timeframe")
    op.create_unique_constraint("uq_price_bar_asset_ts", "price_bars", ["asset_id", "timestamp"])
