from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AlertLog(Base):
    __tablename__ = "alert_log"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False, index=True)

    # "signal_change" | "score_high" | "score_low"
    rule_key: Mapped[str] = mapped_column(String(50), nullable=False)

    fired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Payload sanitizado enviado ao canal — sem token, sem chat_id
    payload_snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    # "sent" | "dry_run" | "failed" | "skipped_duplicate"
    delivery_status: Mapped[str] = mapped_column(String(30), nullable=False)

    is_dry_run: Mapped[bool] = mapped_column(Boolean, nullable=False)

    report_run_id: Mapped[int | None] = mapped_column(ForeignKey("report_runs.id"), nullable=True)
    signal_id: Mapped[int | None] = mapped_column(ForeignKey("signals.id"), nullable=True)

    asset = relationship("Asset", lazy="select")
    report_run = relationship("ReportRun", lazy="select")
