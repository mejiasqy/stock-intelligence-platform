from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AssetCreate(BaseModel):
    symbol: str
    name: str
    exchange: str = "B3"
    asset_type: str = "stock"


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    name: str
    exchange: str
    asset_type: str
    created_at: datetime
