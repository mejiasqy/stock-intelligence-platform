from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False, index=True)

    strategy_name: Mapped[str] = mapped_column(String(50), nullable=False)
    strategy_version: Mapped[str] = mapped_column(String(20), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(20), nullable=False)

    data_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)

    initial_capital: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    transaction_cost_bps: Mapped[int] = mapped_column(BigInteger, nullable=False)
    slippage_bps: Mapped[int] = mapped_column(BigInteger, nullable=False)
    risk_free_rate_pct: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    parameters_snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    status: Mapped[str] = mapped_column(String(20), nullable=False)

    final_equity: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    total_return_pct: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    annualized_return_pct: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    volatility_pct: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    sharpe_ratio: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    max_drawdown_pct: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    win_rate_pct: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    profit_factor: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    trade_count: Mapped[int | None] = mapped_column(nullable=True)
    exposure_pct: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    benchmark_return_pct: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    equity_curve_json: Mapped[list | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    asset = relationship("Asset", lazy="select")
    trades: Mapped[list["BacktestTrade"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "BacktestTrade", back_populates="run", lazy="select"
    )
