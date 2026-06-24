import pandas as pd
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.db.models.indicator_snapshot import IndicatorSnapshot
from app.db.models.price_bar import PriceBar
from app.domain.indicators.engine import CALCULATION_VERSION, compute

# Janela máxima de candles carregados — suficiente para todos os indicadores (61) com margem.
_LOAD_LIMIT = 300

_DEFAULT_TIMEFRAME = "1d"
_DEFAULT_SOURCE = "yfinance"

# Campos que são sobrescritos no upsert (exclui as colunas da constraint de unicidade).
_UPSERT_FIELDS = (
    "calculation_version",
    "candles_used",
    "status",
    "last_close",
    "last_volume",
    "sma_20",
    "sma_50",
    "ema_20",
    "rsi_14",
    "macd",
    "macd_signal",
    "macd_histogram",
    "bollinger_upper",
    "bollinger_middle",
    "bollinger_lower",
    "volume_avg_20",
    "vol_annualized_20d",
    "max_drawdown_60d",
    "current_drawdown_60d",
    "return_1d",
    "return_5d",
    "return_20d",
    "return_60d",
    "insufficient_fields",
)


def calculate_and_persist(
    db: Session,
    asset_id: int,
    timeframe: str = _DEFAULT_TIMEFRAME,
    source: str = _DEFAULT_SOURCE,
) -> IndicatorSnapshot:
    """Calcula indicadores sobre os candles disponíveis e persiste/atualiza o snapshot.

    Idempotente: chamadas repetidas para o mesmo (asset_id, timeframe, source)
    sobrescrevem o snapshot anterior; não acumula histórico de versões.
    """
    bars: list[PriceBar] = (
        db.query(PriceBar)
        .filter(
            PriceBar.asset_id == asset_id,
            PriceBar.timeframe == timeframe,
            PriceBar.source == source,
        )
        .order_by(PriceBar.timestamp.asc())
        .limit(_LOAD_LIMIT)
        .all()
    )

    close = pd.Series([float(b.close) for b in bars], dtype="float64")
    volume = pd.Series([float(b.volume) for b in bars], dtype="float64")

    payload = compute(close, volume)

    row = {
        "asset_id": asset_id,
        "timeframe": timeframe,
        "source": source,
        "calculation_version": CALCULATION_VERSION,
        "candles_used": payload.candles_used,
        "status": payload.status,
        "last_close": payload.last_close,
        "last_volume": payload.last_volume,
        "sma_20": payload.sma_20,
        "sma_50": payload.sma_50,
        "ema_20": payload.ema_20,
        "rsi_14": payload.rsi_14,
        "macd": payload.macd,
        "macd_signal": payload.macd_signal,
        "macd_histogram": payload.macd_histogram,
        "bollinger_upper": payload.bollinger_upper,
        "bollinger_middle": payload.bollinger_middle,
        "bollinger_lower": payload.bollinger_lower,
        "volume_avg_20": payload.volume_avg_20,
        "vol_annualized_20d": payload.vol_annualized_20d,
        "max_drawdown_60d": payload.max_drawdown_60d,
        "current_drawdown_60d": payload.current_drawdown_60d,
        "return_1d": payload.return_1d,
        "return_5d": payload.return_5d,
        "return_20d": payload.return_20d,
        "return_60d": payload.return_60d,
        "insufficient_fields": payload.insufficient_fields or None,
    }

    stmt = pg_insert(IndicatorSnapshot).values([row])
    stmt = stmt.on_conflict_do_update(
        constraint="uq_snapshot_asset_tf_src",
        set_={
            "calculated_at": func.now(),
            **{field: stmt.excluded[field] for field in _UPSERT_FIELDS},
        },
    )
    db.execute(stmt)
    db.commit()

    snapshot: IndicatorSnapshot = (
        db.query(IndicatorSnapshot)
        .filter(
            IndicatorSnapshot.asset_id == asset_id,
            IndicatorSnapshot.timeframe == timeframe,
            IndicatorSnapshot.source == source,
        )
        .one()
    )
    return snapshot
