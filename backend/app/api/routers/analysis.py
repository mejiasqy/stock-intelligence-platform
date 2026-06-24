from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.core.config import settings
from app.db.models.asset import Asset
from app.db.models.indicator_snapshot import IndicatorSnapshot
from app.schemas.indicator_snapshot import IndicatorSnapshotRead
from app.services.analysis_service import calculate_and_persist

router = APIRouter(prefix="/assets", tags=["analysis"])


def _require_api_key(x_api_key: str = Header(..., alias="X-Api-Key")) -> None:
    if x_api_key != settings.api_secret_key:
        raise HTTPException(status_code=401, detail="invalid_api_key")


def _get_asset_or_404(symbol: str, db: Session) -> Asset:
    asset = db.query(Asset).filter(Asset.symbol == symbol.upper()).first()
    if asset is None:
        raise HTTPException(status_code=404, detail="asset_not_found")
    return asset


@router.get("/{symbol}/analysis", response_model=IndicatorSnapshotRead)
def get_analysis(symbol: str, db: Session = Depends(get_db)) -> IndicatorSnapshot:
    """Retorna o snapshot de indicadores mais recente para o ativo.

    Somente leitura — não dispara recálculo.
    Retorna 404 se nenhum snapshot foi calculado ainda.
    """
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
    dependencies=[Depends(_require_api_key)],
)
def recalculate_analysis(symbol: str, db: Session = Depends(get_db)) -> IndicatorSnapshot:
    """Força recálculo e persistência do snapshot de indicadores.

    Requer o header `X-Api-Key` com o valor de `API_SECRET_KEY`.
    Idempotente: sobrescreve o snapshot anterior para o mesmo ativo/timeframe/source.
    """
    asset = _get_asset_or_404(symbol, db)
    return calculate_and_persist(db, asset_id=asset.id)
