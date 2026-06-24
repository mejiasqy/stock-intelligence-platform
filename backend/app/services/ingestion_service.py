from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.db.models.asset import Asset
from app.db.models.price_bar import PriceBar
from app.providers.market_data.yfinance_provider import YFinanceProvider
from app.schemas.price_bar import IngestionResult

_DEFAULT_TIMEFRAME = "1d"
_DEFAULT_SOURCE = "yfinance"


def get_or_create_asset(db: Session, symbol: str, name: str) -> Asset:
    asset = db.query(Asset).filter(Asset.symbol == symbol).first()
    if asset is None:
        asset = Asset(symbol=symbol, name=name)
        db.add(asset)
        db.flush()
    return asset


def ingest_prices(
    db: Session,
    symbol: str,
    days: int = 365,
    provider: YFinanceProvider | None = None,
    timeframe: str = _DEFAULT_TIMEFRAME,
    source: str = _DEFAULT_SOURCE,
) -> IngestionResult:
    if provider is None:
        provider = YFinanceProvider()

    df = provider.fetch_ohlcv(symbol, days)

    if df.empty:
        return IngestionResult(symbol=symbol, inserted=0, skipped=0)

    asset = get_or_create_asset(db, symbol, name=symbol)

    rows = [
        {
            "asset_id": asset.id,
            "timeframe": timeframe,
            "source": source,
            "timestamp": row["timestamp"],
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": int(row["volume"]),
        }
        for _, row in df.iterrows()
    ]

    existing = (
        db.query(PriceBar)
        .filter(
            PriceBar.asset_id == asset.id,
            PriceBar.timeframe == timeframe,
            PriceBar.source == source,
        )
        .count()
    )

    stmt = pg_insert(PriceBar).values(rows)
    stmt = stmt.on_conflict_do_nothing(
        index_elements=["asset_id", "timeframe", "timestamp", "source"]
    )
    db.execute(stmt)
    db.commit()

    after = (
        db.query(PriceBar)
        .filter(
            PriceBar.asset_id == asset.id,
            PriceBar.timeframe == timeframe,
            PriceBar.source == source,
        )
        .count()
    )
    inserted = after - existing
    skipped = len(rows) - inserted

    return IngestionResult(
        symbol=symbol,
        inserted=inserted,
        skipped=skipped,
        asset_id=asset.id,
    )
