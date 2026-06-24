from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DEFAULT_SOURCE, DEFAULT_TIMEFRAME
from app.db.base import Base


class IndicatorSnapshot(Base):
    __tablename__ = "indicator_snapshots"
    __table_args__ = (
        UniqueConstraint("asset_id", "timeframe", "source", name="uq_snapshot_asset_tf_src"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False, index=True)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False, default=DEFAULT_TIMEFRAME)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default=DEFAULT_SOURCE)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    calculation_version: Mapped[str] = mapped_column(String(20), nullable=False)
    candles_used: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    # Returns
    return_1d: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    return_5d: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    return_20d: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    return_60d: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)

    # Moving averages
    sma_20: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    sma_50: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    ema_20: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)

    # Oscillators
    rsi_14: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    macd: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    macd_signal: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    macd_histogram: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)

    # Bollinger Bands
    bollinger_upper: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    bollinger_middle: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    bollinger_lower: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)

    # Volume
    volume_avg_20: Mapped[float | None] = mapped_column(Numeric(20, 2), nullable=True)
    last_volume: Mapped[float | None] = mapped_column(Numeric(20, 2), nullable=True)

    # Last candle price (necessário para scoring)
    last_close: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)

    # Risk
    vol_annualized_20d: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    max_drawdown_60d: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    current_drawdown_60d: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)

    # {campo: mínimo_requerido} dos campos não disponíveis neste snapshot.
    insufficient_fields: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    asset = relationship("Asset", lazy="select")
