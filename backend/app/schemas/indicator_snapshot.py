from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IndicatorSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: int
    timeframe: str
    source: str
    calculated_at: datetime
    calculation_version: str
    candles_used: int
    status: str

    sma_20: float | None
    sma_50: float | None
    ema_20: float | None
    rsi_14: float | None
    macd: float | None
    macd_signal: float | None
    macd_histogram: float | None
    bollinger_upper: float | None
    bollinger_middle: float | None
    bollinger_lower: float | None
    volume_avg_20: float | None
    last_volume: float | None
    last_close: float | None
    vol_annualized_20d: float | None
    max_drawdown_60d: float | None
    current_drawdown_60d: float | None
    return_1d: float | None
    return_5d: float | None
    return_20d: float | None
    return_60d: float | None

    insufficient_fields: dict[str, int] | None
