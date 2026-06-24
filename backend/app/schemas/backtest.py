from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class BacktestRunRequest(BaseModel):
    symbol: str
    start_date: date | None = None
    end_date: date | None = None
    initial_capital: float = Field(default=100_000.0, gt=0)
    strategy_name: str = "sma_crossover"
    transaction_cost_bps: int = Field(default=10, ge=0)
    slippage_bps: int = Field(default=10, ge=0)
    risk_free_rate_pct: float = Field(default=0.0, ge=0.0)


class BacktestTradeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    backtest_run_id: int
    entry_timestamp: datetime
    exit_timestamp: datetime
    entry_price: float
    exit_price: float
    executed_entry_price: float
    executed_exit_price: float
    quantity: int
    gross_pnl: float
    net_pnl: float
    fees_paid: float
    reason_entry: str
    reason_exit: str


class BacktestRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: int
    strategy_name: str
    strategy_version: str
    engine_version: str
    data_start: datetime
    data_end: datetime
    timeframe: str
    source: str
    initial_capital: float
    transaction_cost_bps: int
    slippage_bps: int
    risk_free_rate_pct: float
    parameters_snapshot_json: dict
    status: str
    final_equity: float | None
    total_return_pct: float | None
    annualized_return_pct: float | None
    volatility_pct: float | None
    sharpe_ratio: float | None
    max_drawdown_pct: float | None
    win_rate_pct: float | None
    profit_factor: float | None
    trade_count: int | None
    exposure_pct: float | None
    benchmark_return_pct: float | None
    equity_curve_json: list | None
    created_at: datetime
