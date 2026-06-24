from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.db.models.asset import Asset
from app.db.models.price_bar import PriceBar
from app.schemas.asset import AssetCreate, AssetRead
from app.schemas.price_bar import IngestionRequest, IngestionResult, PriceBarRead
from app.services.ingestion_service import ingest_prices

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("", response_model=list[AssetRead])
def list_assets(db: Session = Depends(get_db)) -> list[Asset]:
    return db.query(Asset).order_by(Asset.symbol).all()


@router.post("", response_model=AssetRead, status_code=201)
def create_asset(payload: AssetCreate, db: Session = Depends(get_db)) -> Asset:
    existing = db.query(Asset).filter(Asset.symbol == payload.symbol).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Asset '{payload.symbol}' already exists")
    asset = Asset(**payload.model_dump())
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.get("/{symbol}/prices", response_model=list[PriceBarRead])
def get_prices(
    symbol: str,
    limit: int = 252,
    db: Session = Depends(get_db),
) -> list[PriceBar]:
    asset = db.query(Asset).filter(Asset.symbol == symbol.upper()).first()
    if asset is None:
        raise HTTPException(status_code=404, detail=f"Asset '{symbol}' not found")
    bars: list[PriceBar] = (
        db.query(PriceBar)
        .filter(PriceBar.asset_id == asset.id)
        .order_by(PriceBar.timestamp.desc())
        .limit(limit)
        .all()
    )
    return bars


@router.post("/ingestion/run", response_model=IngestionResult)
def run_ingestion(
    payload: IngestionRequest,
    db: Session = Depends(get_db),
) -> IngestionResult:
    return ingest_prices(db, symbol=payload.symbol.upper(), days=payload.days)
