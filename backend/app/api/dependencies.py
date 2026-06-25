from collections.abc import Generator

from fastapi import Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_api_key(x_api_key: str | None = Header(None, alias="X-Api-Key")) -> None:
    """Rejeita requisições sem X-Api-Key válida com 401."""
    if x_api_key is None or x_api_key != settings.api_secret_key:
        raise HTTPException(status_code=401, detail="unauthorized")


def get_pagination_params(
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
        description="Itens por página (máx 100)",
    ),
    offset: int = Query(default=0, ge=0, description="Itens a pular"),
) -> dict[str, int]:
    return {"limit": limit, "offset": offset}


def get_trades_pagination_params(
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
        description="Itens por página (máx 500)",
    ),
    offset: int = Query(default=0, ge=0, description="Itens a pular"),
) -> dict[str, int]:
    return {"limit": limit, "offset": offset}


PaginationDep = Depends(get_pagination_params)
TradesPaginationDep = Depends(get_trades_pagination_params)
