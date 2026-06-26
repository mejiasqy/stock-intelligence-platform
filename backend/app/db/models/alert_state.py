from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AlertState(Base):
    __tablename__ = "alert_state"
    __table_args__ = (UniqueConstraint("asset_id", "rule_key", name="uq_alert_state_asset_rule"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False)

    # "signal_change" | "score_high" | "score_low"
    rule_key: Mapped[str] = mapped_column(String(50), nullable=False)

    # Ex: {"signal_type": "bullish"} ou {"score": 72.5}
    last_observed_value_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    asset = relationship("Asset", lazy="select")
