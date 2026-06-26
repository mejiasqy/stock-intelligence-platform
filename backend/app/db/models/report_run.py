from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ReportRun(Base):
    __tablename__ = "report_runs"
    __table_args__ = (
        UniqueConstraint(
            "asset_id",
            "report_type",
            "report_date",
            "input_fingerprint",
            name="uq_report_run_asset_type_date_fp",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False, index=True)
    signal_id: Mapped[int | None] = mapped_column(ForeignKey("signals.id"), nullable=True)

    # "daily" (pipeline) ou "on_demand" (POST /generate)
    report_type: Mapped[str] = mapped_column(String(30), nullable=False, default="daily")

    generated_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_fallback: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # "generated" | "fallback" | "failed"
    generation_status: Mapped[str] = mapped_column(String(20), nullable=False)

    # Nunca contém segredo; registra apenas falha técnica sanitizada
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(20), nullable=False)

    # "ok" | "partial" | "insufficient_data" — herdado do IndicatorSnapshot.status
    data_quality: Mapped[str] = mapped_column(String(20), nullable=False)

    # Contexto exato enviado ao provider; nunca contém segredos
    input_snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    # SHA-256 hex(64) do JSON canônico do contexto
    input_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)

    # Data UTC usada para idempotência
    report_date: Mapped[date] = mapped_column(Date, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    asset = relationship("Asset", lazy="select")
    signal = relationship("Signal", lazy="select")
