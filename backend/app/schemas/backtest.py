from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BacktestRunRequest(BaseModel):
    symbol: str = Field(
        pattern=r"^[A-Z0-9\.]{1,20}$",
        description="Símbolo do ativo (ex: PETR4.SA)",
        examples=["PETR4.SA"],
    )
    start_date: date | None = Field(default=None, description="Data inicial do período de backtest")
    end_date: date | None = Field(default=None, description="Data final do período de backtest")
    initial_capital: float = Field(default=100_000.0, gt=0, description="Capital inicial em reais")
    strategy_name: str = Field(default="sma_crossover", description="Nome da estratégia")
    transaction_cost_bps: int = Field(default=10, ge=0, description="Custo de transação em bps")
    slippage_bps: int = Field(default=10, ge=0, description="Slippage em bps")
    risk_free_rate_pct: float = Field(
        default=0.0, ge=0.0, description="Taxa livre de risco (% ao ano)"
    )

    @model_validator(mode="after")
    def validate_date_range(self) -> "BacktestRunRequest":
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        return self


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


class BacktestRunSummary(BaseModel):
    """Resumo de um backtest — sem equity_curve para uso em listagens."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: int
    symbol: str
    strategy_name: str
    strategy_version: str
    engine_version: str
    data_start: datetime
    data_end: datetime
    initial_capital: float
    status: str
    total_return_pct: float | None
    sharpe_ratio: float | None
    max_drawdown_pct: float | None
    trade_count: int | None
    created_at: datetime


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
