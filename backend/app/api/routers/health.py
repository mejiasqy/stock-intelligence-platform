from fastapi import APIRouter
from pydantic import BaseModel

from app.db.session import check_connection

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str


class ReadyResponse(BaseModel):
    status: str
    database: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", version="0.1.0")


@router.get("/ready", response_model=ReadyResponse)
async def ready_check() -> ReadyResponse:
    db_ok = check_connection()
    return ReadyResponse(
        status="ok" if db_ok else "degraded",
        database="connected" if db_ok else "unavailable",
    )
