from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.db.models.indicator_snapshot import IndicatorSnapshot
from app.db.models.signal import Signal
from app.domain.scoring.engine import SCORING_VERSION, score

_UPSERT_FIELDS = (
    "snapshot_id",
    "signal_type",
    "strength",
    "score",
    "reason_codes",
    "pillar_scores",
)


def _f(value: object) -> float | None:
    return float(value) if value is not None else None  # type: ignore[arg-type]


def score_and_persist(
    db: Session,
    asset_id: int,
    snapshot: IndicatorSnapshot,
) -> Signal:
    """Calcula o sinal de mercado e persiste/atualiza na tabela signals.

    Idempotente: upsert por (asset_id, strategy_version).
    """
    payload = score(
        last_close=_f(snapshot.last_close),
        last_volume=_f(snapshot.last_volume),
        sma_20=_f(snapshot.sma_20),
        sma_50=_f(snapshot.sma_50),
        ema_20=_f(snapshot.ema_20),
        rsi_14=_f(snapshot.rsi_14),
        macd=_f(snapshot.macd),
        macd_signal=_f(snapshot.macd_signal),
        bollinger_upper=_f(snapshot.bollinger_upper),
        bollinger_middle=_f(snapshot.bollinger_middle),
        bollinger_lower=_f(snapshot.bollinger_lower),
        volume_avg_20=_f(snapshot.volume_avg_20),
        vol_annualized_20d=_f(snapshot.vol_annualized_20d),
        max_drawdown_60d=_f(snapshot.max_drawdown_60d),
        current_drawdown_60d=_f(snapshot.current_drawdown_60d),
        return_1d=_f(snapshot.return_1d),
        return_5d=_f(snapshot.return_5d),
        return_20d=_f(snapshot.return_20d),
        return_60d=_f(snapshot.return_60d),
    )

    row = {
        "asset_id": asset_id,
        "snapshot_id": snapshot.id,
        "strategy_version": SCORING_VERSION,
        "signal_type": payload.signal_type,
        "strength": payload.strength,
        "score": payload.score,
        "reason_codes": payload.reason_codes,
        "pillar_scores": payload.pillar_scores,
    }

    stmt = pg_insert(Signal).values([row])
    stmt = stmt.on_conflict_do_update(
        constraint="uq_signal_asset_strategy",
        set_={
            "calculated_at": func.now(),
            **{field: stmt.excluded[field] for field in _UPSERT_FIELDS},
        },
    )
    db.execute(stmt)
    db.commit()

    signal: Signal = (
        db.query(Signal)
        .filter(
            Signal.asset_id == asset_id,
            Signal.strategy_version == SCORING_VERSION,
        )
        .one()
    )
    return signal
