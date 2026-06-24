from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PriceBarRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: int
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class IngestionRequest(BaseModel):
    symbol: str
    days: int = 365


class IngestionResult(BaseModel):
    symbol: str
    inserted: int
    skipped: int
