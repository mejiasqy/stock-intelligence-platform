from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SignalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: int
    snapshot_id: int | None
    strategy_version: str
    signal_type: str
    strength: float
    score: float
    reason_codes: dict[str, bool]
    pillar_scores: dict[str, float]
    calculated_at: datetime


class RankingEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asset_id: int
    symbol: str
    signal_type: str
    score: float
    strength: float
    strategy_version: str
    calculated_at: datetime
