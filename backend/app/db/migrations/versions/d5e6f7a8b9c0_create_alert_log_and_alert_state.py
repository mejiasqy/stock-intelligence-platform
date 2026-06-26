"""create_alert_log_and_alert_state

Revision ID: d5e6f7a8b9c0
Revises: c9d0e1f2a3b4
Create Date: 2026-06-25 09:01:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d5e6f7a8b9c0"
down_revision: str | Sequence[str] | None = "c9d0e1f2a3b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "alert_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("rule_key", sa.String(length=50), nullable=False),
        sa.Column(
            "fired_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("payload_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("delivery_status", sa.String(length=30), nullable=False),
        sa.Column("is_dry_run", sa.Boolean(), nullable=False),
        sa.Column("report_run_id", sa.Integer(), nullable=True),
        sa.Column("signal_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["report_run_id"], ["report_runs.id"]),
        sa.ForeignKeyConstraint(["signal_id"], ["signals.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alert_log_id"), "alert_log", ["id"], unique=False)
    op.create_index(op.f("ix_alert_log_asset_id"), "alert_log", ["asset_id"], unique=False)
    # Índice composto para a query de deduplicação: filtra por asset_id, rule_key e fired_at
    op.create_index(
        "ix_alert_log_asset_rule_fired",
        "alert_log",
        ["asset_id", "rule_key", "fired_at"],
        unique=False,
    )

    op.create_table(
        "alert_state",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("rule_key", sa.String(length=50), nullable=False),
        sa.Column("last_observed_value_json", sa.JSON(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_id", "rule_key", name="uq_alert_state_asset_rule"),
    )
    op.create_index(op.f("ix_alert_state_id"), "alert_state", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_alert_state_id"), table_name="alert_state")
    op.drop_table("alert_state")
    op.drop_index("ix_alert_log_asset_rule_fired", table_name="alert_log")
    op.drop_index(op.f("ix_alert_log_asset_id"), table_name="alert_log")
    op.drop_index(op.f("ix_alert_log_id"), table_name="alert_log")
    op.drop_table("alert_log")
