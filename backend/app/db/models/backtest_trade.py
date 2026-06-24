from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BacktestTrade(Base):
    __tablename__ = "backtest_trades"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    backtest_run_id: Mapped[int] = mapped_column(
        ForeignKey("backtest_runs.id"), nullable=False, index=True
    )

    entry_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    exit_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    entry_price: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    exit_price: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    executed_entry_price: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    executed_exit_price: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    quantity: Mapped[int] = mapped_column(BigInteger, nullable=False)
    gross_pnl: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    net_pnl: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    fees_paid: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    reason_entry: Mapped[str] = mapped_column(String(50), nullable=False)
    reason_exit: Mapped[str] = mapped_column(String(50), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    run = relationship("BacktestRun", back_populates="trades")
