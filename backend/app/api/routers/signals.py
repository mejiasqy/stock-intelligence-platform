from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.core.config import settings
from app.db.models.asset import Asset
from app.db.models.signal import Signal
from app.schemas.signal import RankingEntry, SignalRead
from app.services.analysis_service import calculate_and_persist
from app.services.scoring_service import SCORING_VERSION, score_and_persist

router = APIRouter(tags=["signals"])


def _require_api_key(x_api_key: str = Header(..., alias="X-Api-Key")) -> None:
    if x_api_key != settings.api_secret_key:
        raise HTTPException(status_code=401, detail="invalid_api_key")


def _get_asset_or_404(symbol: str, db: Session) -> Asset:
    asset = db.query(Asset).filter(Asset.symbol == symbol.upper()).first()
    if asset is None:
        raise HTTPException(status_code=404, detail="asset_not_found")
    return asset


@router.get("/assets/{symbol}/signal", response_model=SignalRead)
def get_signal(symbol: str, db: Session = Depends(get_db)) -> Signal:
    """Retorna o sinal de mercado mais recente para o ativo.

    Somente leitura — não dispara recálculo.
    Retorna 404 se nenhum sinal foi calculado ainda.
    """
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
    dependencies=[Depends(_require_api_key)],
)
def recalculate_signal(symbol: str, db: Session = Depends(get_db)) -> Signal:
    """Força recálculo de indicadores e sinal de mercado para o ativo.

    Requer o header `X-Api-Key`. Idempotente — sobrescreve o sinal anterior.
    """
    asset = _get_asset_or_404(symbol, db)
    snapshot = calculate_and_persist(db, asset_id=asset.id)
    return score_and_persist(db, asset_id=asset.id, snapshot=snapshot)


@router.get("/rankings", response_model=list[RankingEntry])
def get_rankings(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> list[RankingEntry]:
    """Retorna ativos com sinal calculado, ordenados por score decrescente.

    Somente ativos que já possuem ao menos um sinal persistido aparecem aqui.
    """
    rows = (
        db.query(Signal, Asset)
        .join(Asset, Signal.asset_id == Asset.id)
        .filter(Signal.strategy_version == SCORING_VERSION)
        .order_by(Signal.score.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
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
