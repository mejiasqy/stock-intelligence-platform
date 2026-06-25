from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_pagination_params, require_api_key
from app.core.rate_limiter import limiter
from app.db.models.asset import Asset
from app.db.models.signal import Signal
from app.schemas.pagination import PaginatedResponse, PaginationMeta
from app.schemas.signal import RankingEntry, SignalRead
from app.services.analysis_service import calculate_and_persist
from app.services.scoring_service import SCORING_VERSION, score_and_persist

router = APIRouter(tags=["signals"])

_RANKING_SORT_FIELDS = {"score"}


def _get_asset_or_404(symbol: str, db: Session) -> Asset:
    asset = db.query(Asset).filter(Asset.symbol == symbol.upper()).first()
    if asset is None:
        raise HTTPException(status_code=404, detail="asset_not_found")
    return asset


@router.get(
    "/assets/{symbol}/signal",
    response_model=SignalRead,
    summary="Sinal analítico do ativo",
    description="Retorna o sinal mais recente. Somente leitura.",
    responses={404: {"description": "Ativo não encontrado ou sinal indisponível"}},
)
def get_signal(symbol: str, db: Session = Depends(get_db)) -> Signal:
    asset = _get_asset_or_404(symbol, db)
    signal = (
        db.query(Signal)
        .filter(Signal.asset_id == asset.id)
        .order_by(Signal.calculated_at.desc())
        .first()
    )
    if signal is None:
        raise HTTPException(status_code=404, detail="no_signal_available")
    return signal


@router.post(
    "/assets/{symbol}/signal/recalculate",
    response_model=SignalRead,
    dependencies=[Depends(require_api_key)],
    summary="Recalcular sinal do ativo",
    description="Força recálculo de indicadores e sinal. Idempotente. Requer `X-Api-Key`.",
    responses={
        401: {"description": "API key inválida ou ausente"},
        404: {"description": "Ativo não encontrado"},
    },
)
def recalculate_signal(symbol: str, db: Session = Depends(get_db)) -> Signal:
    asset = _get_asset_or_404(symbol, db)
    snapshot = calculate_and_persist(db, asset_id=asset.id)
    return score_and_persist(db, asset_id=asset.id, snapshot=snapshot)


@router.get(
    "/rankings",
    response_model=PaginatedResponse[RankingEntry],
    summary="Ranking de ativos por score",
    description=(
        "Retorna ativos com sinal calculado, ordenados por score. "
        "Filtrável por tipo de sinal e faixa de score."
    ),
    responses={422: {"description": "Parâmetros inválidos"}},
)
@limiter.limit("30/minute")
def get_rankings(
    request: Request,
    signal_type: str | None = Query(
        None,
        pattern="^(bullish|bearish|neutral)$",
        description="Filtrar por tipo de sinal",
    ),
    min_score: float | None = Query(None, ge=0.0, le=100.0, description="Score mínimo"),
    max_score: float | None = Query(None, ge=0.0, le=100.0, description="Score máximo"),
    sort_by: Literal["score"] = Query("score", description="Campo de ordenação"),
    sort_order: Literal["asc", "desc"] = Query("desc", description="Direção da ordenação"),
    pagination: dict = Depends(get_pagination_params),
    db: Session = Depends(get_db),
) -> dict:
    limit, offset = pagination["limit"], pagination["offset"]

    query = (
        db.query(Signal, Asset)
        .join(Asset, Signal.asset_id == Asset.id)
        .filter(Signal.strategy_version == SCORING_VERSION)
    )

    if signal_type is not None:
        query = query.filter(Signal.signal_type == signal_type)
    if min_score is not None:
        query = query.filter(Signal.score >= min_score)
    if max_score is not None:
        query = query.filter(Signal.score <= max_score)

    order_col = Signal.score
    query = query.order_by(order_col.asc() if sort_order == "asc" else order_col.desc())

    total: int = query.count()
    rows = query.offset(offset).limit(limit).all()

    items = [
        RankingEntry(
            asset_id=signal.asset_id,
            symbol=asset.symbol,
            signal_type=signal.signal_type,
            score=float(signal.score),
            strength=float(signal.strength),
            strategy_version=signal.strategy_version,
            calculated_at=signal.calculated_at,
        )
        for signal, asset in rows
    ]
    return {
        "items": items,
        "pagination": PaginationMeta(limit=limit, offset=offset, total=total),
    }
