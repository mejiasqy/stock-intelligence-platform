from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_api_key
from app.core.rate_limiter import limiter
from app.db.models.asset import Asset
from app.db.models.indicator_snapshot import IndicatorSnapshot
from app.schemas.indicator_snapshot import IndicatorSnapshotRead
from app.services.analysis_service import calculate_and_persist

router = APIRouter(prefix="/assets", tags=["analysis"])


def _get_asset_or_404(symbol: str, db: Session) -> Asset:
    asset = db.query(Asset).filter(Asset.symbol == symbol.upper()).first()
    if asset is None:
        raise HTTPException(status_code=404, detail="asset_not_found")
    return asset


@router.get(
    "/{symbol}/analysis",
    response_model=IndicatorSnapshotRead,
    summary="Indicadores técnicos do ativo",
    description="Retorna o snapshot de indicadores mais recente. Somente leitura.",
    responses={
        404: {"description": "Ativo não encontrado ou snapshot indisponível"},
    },
)
@limiter.limit("30/minute")
def get_analysis(
    request: Request,
    symbol: str,
    db: Session = Depends(get_db),
) -> IndicatorSnapshot:
    asset = _get_asset_or_404(symbol, db)
    snapshot = (
        db.query(IndicatorSnapshot)
        .filter(IndicatorSnapshot.asset_id == asset.id)
        .order_by(IndicatorSnapshot.calculated_at.desc())
        .first()
    )
    if snapshot is None:
        raise HTTPException(status_code=404, detail="no_snapshot_available")
    return snapshot


@router.post(
    "/{symbol}/analysis/recalculate",
    response_model=IndicatorSnapshotRead,
    dependencies=[Depends(require_api_key)],
    summary="Recalcular indicadores do ativo",
    description="Força recálculo e persistência do snapshot. Idempotente. Requer `X-Api-Key`.",
    responses={
        401: {"description": "API key inválida ou ausente"},
        404: {"description": "Ativo não encontrado"},
    },
)
def recalculate_analysis(symbol: str, db: Session = Depends(get_db)) -> IndicatorSnapshot:
    asset = _get_asset_or_404(symbol, db)
    return calculate_and_persist(db, asset_id=asset.id)
