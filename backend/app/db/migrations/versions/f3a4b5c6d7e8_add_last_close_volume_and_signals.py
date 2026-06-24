"""add_last_close_volume_to_snapshots_and_create_signals

Revision ID: f3a4b5c6d7e8
Revises: d1e2f3a4b5c6
Create Date: 2026-06-24 09:00:00.000000

- Adiciona last_close e last_volume em indicator_snapshots (D25 Opção A)
- Cria tabela signals com UNIQUE(asset_id, strategy_version)
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f3a4b5c6d7e8"
down_revision: str | None = "d1e2f3a4b5c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "indicator_snapshots",
        sa.Column("last_close", sa.Numeric(precision=18, scale=6), nullable=True),
    )
    op.add_column(
        "indicator_snapshots",
        sa.Column("last_volume", sa.Numeric(precision=20, scale=2), nullable=True),
    )

    op.create_table(
        "signals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("snapshot_id", sa.Integer(), nullable=True),
        sa.Column("strategy_version", sa.String(length=20), nullable=False),
        sa.Column("signal_type", sa.String(length=10), nullable=False),
        sa.Column("strength", sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column("score", sa.Numeric(precision=7, scale=4), nullable=False),
        sa.Column("reason_codes", sa.JSON(), nullable=False),
        sa.Column("pillar_scores", sa.JSON(), nullable=False),
        sa.Column(
            "calculated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["snapshot_id"], ["indicator_snapshots.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_id", "strategy_version", name="uq_signal_asset_strategy"),
    )
    op.create_index("ix_signals_id", "signals", ["id"])
    op.create_index("ix_signals_asset_id", "signals", ["asset_id"])


def downgrade() -> None:
    op.drop_index("ix_signals_asset_id", table_name="signals")
    op.drop_index("ix_signals_id", table_name="signals")
    op.drop_table("signals")
    op.drop_column("indicator_snapshots", "last_volume")
    op.drop_column("indicator_snapshots", "last_close")
