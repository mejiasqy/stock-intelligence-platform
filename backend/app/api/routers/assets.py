from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db,
    get_pagination_params,
    get_trades_pagination_params,
    require_api_key,
)
from app.core.rate_limiter import limiter
from app.db.models.asset import Asset
from app.db.models.price_bar import PriceBar
from app.schemas.asset import AssetCreate, AssetRead
from app.schemas.pagination import PaginatedResponse, PaginationMeta
from app.schemas.price_bar import IngestionRequest, IngestionResult, PriceBarRead
from app.services.analysis_service import calculate_and_persist
from app.services.ingestion_service import ingest_prices
from app.services.scoring_service import score_and_persist

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get(
    "",
    response_model=PaginatedResponse[AssetRead],
    summary="Listar ativos",
    description="Retorna todos os ativos cadastrados, paginados.",
    responses={422: {"description": "Parâmetros de paginação inválidos"}},
)
@limiter.limit("120/minute")
def list_assets(
    request: Request,
    pagination: dict = Depends(get_pagination_params),
    db: Session = Depends(get_db),
) -> dict:
    limit, offset = pagination["limit"], pagination["offset"]
    total: int = db.query(Asset).count()
    items = db.query(Asset).order_by(Asset.symbol).offset(offset).limit(limit).all()
    return {
        "items": items,
        "pagination": PaginationMeta(limit=limit, offset=offset, total=total),
    }


@router.post(
    "",
    response_model=AssetRead,
    status_code=201,
    dependencies=[Depends(require_api_key)],
    summary="Cadastrar ativo",
    description="Cria um novo ativo. Requer `X-Api-Key`.",
    responses={
        401: {"description": "API key inválida ou ausente"},
        409: {"description": "Ativo com este símbolo já existe"},
    },
)
def create_asset(payload: AssetCreate, db: Session = Depends(get_db)) -> Asset:
    existing = db.query(Asset).filter(Asset.symbol == payload.symbol).first()
    if existing:
        raise HTTPException(status_code=409, detail="asset_already_exists")
    asset = Asset(**payload.model_dump())
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.get(
    "/{symbol}/prices",
    response_model=PaginatedResponse[PriceBarRead],
    summary="Preços históricos do ativo",
    description="Retorna barras OHLCV do ativo, da mais recente para a mais antiga.",
    responses={404: {"description": "Ativo não encontrado"}},
)
@limiter.limit("120/minute")
def get_prices(
    request: Request,
    symbol: str,
    pagination: dict = Depends(get_trades_pagination_params),
    db: Session = Depends(get_db),
) -> dict:
    asset = db.query(Asset).filter(Asset.symbol == symbol.upper()).first()
    if asset is None:
        raise HTTPException(status_code=404, detail="asset_not_found")
    limit, offset = pagination["limit"], pagination["offset"]
    total: int = db.query(PriceBar).filter(PriceBar.asset_id == asset.id).count()
    bars = (
        db.query(PriceBar)
        .filter(PriceBar.asset_id == asset.id)
        .order_by(PriceBar.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "items": bars,
        "pagination": PaginationMeta(limit=limit, offset=offset, total=total),
    }


@router.post(
    "/ingestion/run",
    response_model=IngestionResult,
    dependencies=[Depends(require_api_key)],
    summary="Executar ingestão de preços",
    description=(
        "Coleta dados históricos do provedor e persiste candles novos. "
        "Dispara recálculo de indicadores e sinal quando há dados novos. "
        "Requer `X-Api-Key`."
    ),
    responses={401: {"description": "API key inválida ou ausente"}},
)
@limiter.limit("10/minute")
def run_ingestion(
    request: Request,
    payload: IngestionRequest,
    db: Session = Depends(get_db),
) -> IngestionResult:
    result = ingest_prices(db, symbol=payload.symbol.upper(), days=payload.days)
    if result.inserted > 0 and result.asset_id is not None:
        snapshot = calculate_and_persist(db, asset_id=result.asset_id)
        score_and_persist(db, asset_id=result.asset_id, snapshot=snapshot)
    return result
