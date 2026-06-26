"""create_report_runs

Revision ID: c9d0e1f2a3b4
Revises: 208463870910
Create Date: 2026-06-25 09:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c9d0e1f2a3b4"
down_revision: str | Sequence[str] | None = "208463870910"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "report_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("signal_id", sa.Integer(), nullable=True),
        sa.Column("report_type", sa.String(length=30), nullable=False),
        sa.Column("generated_text", sa.Text(), nullable=False),
        sa.Column("is_fallback", sa.Boolean(), nullable=False),
        sa.Column("generation_status", sa.String(length=20), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=20), nullable=False),
        sa.Column("data_quality", sa.String(length=20), nullable=False),
        sa.Column("input_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("input_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["signal_id"], ["signals.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "asset_id",
            "report_type",
            "report_date",
            "input_fingerprint",
            name="uq_report_run_asset_type_date_fp",
        ),
    )
    op.create_index(op.f("ix_report_runs_id"), "report_runs", ["id"], unique=False)
    op.create_index(op.f("ix_report_runs_asset_id"), "report_runs", ["asset_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_report_runs_asset_id"), table_name="report_runs")
    op.drop_index(op.f("ix_report_runs_id"), table_name="report_runs")
    op.drop_table("report_runs")
