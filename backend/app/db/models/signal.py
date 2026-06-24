from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Signal(Base):
    __tablename__ = "signals"
    __table_args__ = (
        UniqueConstraint("asset_id", "strategy_version", name="uq_signal_asset_strategy"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False, index=True)
    snapshot_id: Mapped[int | None] = mapped_column(
        ForeignKey("indicator_snapshots.id"), nullable=True
    )
    strategy_version: Mapped[str] = mapped_column(String(20), nullable=False)
    signal_type: Mapped[str] = mapped_column(String(10), nullable=False)  # bullish|bearish|neutral
    strength: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    score: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False)
    reason_codes: Mapped[dict] = mapped_column(JSON, nullable=False)
    pillar_scores: Mapped[dict] = mapped_column(JSON, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    asset = relationship("Asset", lazy="select")
    snapshot = relationship("IndicatorSnapshot", lazy="select")
