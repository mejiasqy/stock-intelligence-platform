"""Constrói o contexto estruturado enviado ao LLM.

Regra D-LLM-2: o contexto contém exclusivamente fatos persistidos ou calculados pelo
sistema para aquele ativo e aquela execução. Proibido incluir: segredos, URLs privadas,
dados de outros ativos, dados externos, campos inferidos pelo frontend.
"""

from typing import Any

from app.db.models.asset import Asset
from app.db.models.indicator_snapshot import IndicatorSnapshot
from app.db.models.signal import Signal
from app.domain.scoring.reason_codes import REASON_CODE_DEFS

# Mapa code → label humano para enriquecer o contexto
_LABEL_BY_CODE: dict[str, str] = {d.code: d.description for d in REASON_CODE_DEFS}

# Constantes de período usadas nos indicadores (usadas pelo validador factual)
KNOWN_PERIOD_CONSTANTS: frozenset[float] = frozenset(
    {1.0, 5.0, 9.0, 14.0, 20.0, 26.0, 50.0, 60.0, 100.0}
)


def build_context(asset: Asset, signal: Signal, snapshot: IndicatorSnapshot) -> dict:
    """Monta o dict canônico de contexto para geração de relatório.

    Todos os valores numéricos são convertidos para float ou None.
    Datetimes são convertidos para ISO string (necessário para fingerprint canônico).
    Nunca inclui: llm_api_key, telegram_bot_token, telegram_chat_id, DATABASE_URL,
    api_secret_key, dados de outros ativos, fontes externas.
    """
    reason_codes_enriched: dict[str, dict] = {}
    raw_codes: dict = signal.reason_codes or {}
    for code, value in raw_codes.items():
        reason_codes_enriched[code] = {
            "value": bool(value),
            "label": _LABEL_BY_CODE.get(code, code),
        }

    def _f(v: Any) -> float | None:
        return float(v) if v is not None else None

    return {
        # Identificação
        "asset_symbol": asset.symbol,
        "asset_name": asset.name,
        # Sinal
        "signal_type": signal.signal_type,
        "strength": _f(signal.strength),
        "score": _f(signal.score),
        "strategy_version": signal.strategy_version,
        "signal_calculated_at": signal.calculated_at.isoformat() if signal.calculated_at else None,
        # Pilares
        "pillar_scores": {k: _f(v) for k, v in (signal.pillar_scores or {}).items()},
        # Reason codes com labels humanos
        "reason_codes": reason_codes_enriched,
        # Qualidade dos dados
        "data_quality": snapshot.status,
        "candles_used": snapshot.candles_used,
        "calculation_version": snapshot.calculation_version,
        "snapshot_calculated_at": (
            snapshot.calculated_at.isoformat() if snapshot.calculated_at else None
        ),
        "insufficient_fields": snapshot.insufficient_fields or {},
        # Indicadores numéricos — None quando dado insuficiente
        "last_close": _f(snapshot.last_close),
        "sma_20": _f(snapshot.sma_20),
        "sma_50": _f(snapshot.sma_50),
        "ema_20": _f(snapshot.ema_20),
        "rsi_14": _f(snapshot.rsi_14),
        "macd": _f(snapshot.macd),
        "macd_signal": _f(snapshot.macd_signal),
        "macd_histogram": _f(snapshot.macd_histogram),
        "bollinger_upper": _f(snapshot.bollinger_upper),
        "bollinger_middle": _f(snapshot.bollinger_middle),
        "bollinger_lower": _f(snapshot.bollinger_lower),
        "volume_avg_20": _f(snapshot.volume_avg_20),
        "last_volume": _f(snapshot.last_volume),
        "vol_annualized_20d": _f(snapshot.vol_annualized_20d),
        "max_drawdown_60d": _f(snapshot.max_drawdown_60d),
        "current_drawdown_60d": _f(snapshot.current_drawdown_60d),
        "return_1d": _f(snapshot.return_1d),
        "return_5d": _f(snapshot.return_5d),
        "return_20d": _f(snapshot.return_20d),
        "return_60d": _f(snapshot.return_60d),
    }
