"""Motor de scoring de sinais de mercado.

SCORING_VERSION deve ser incrementado manualmente a cada mudança em pilares,
pesos, reason_codes ou thresholds. O campo strategy_version na tabela signals
permite manter sinais históricos de versões anteriores.
"""

from dataclasses import dataclass, field

from app.domain.scoring import pillars as p
from app.domain.scoring.reason_codes import evaluate

SCORING_VERSION = "1.0.0"

# Pesos dos pilares (D20): somam 1.0
_WEIGHTS: dict[str, float] = {
    "trend": 0.30,
    "momentum": 0.25,
    "volume": 0.15,
    "risk": 0.15,
    "structure": 0.15,
}

_BULLISH_THRESHOLD = 60.0
_BEARISH_THRESHOLD = 40.0


@dataclass
class SignalPayload:
    score: float  # 0–100
    signal_type: str  # bullish | bearish | neutral
    strength: float  # 0.0–1.0 (distância de 50, normalizada)
    scoring_version: str
    reason_codes: dict[str, bool] = field(default_factory=dict)
    pillar_scores: dict[str, float] = field(default_factory=dict)


def score(
    *,
    last_close: float | None,
    last_volume: float | None,
    sma_20: float | None,
    sma_50: float | None,
    ema_20: float | None,
    rsi_14: float | None,
    macd: float | None,
    macd_signal: float | None,
    bollinger_upper: float | None,
    bollinger_middle: float | None,
    bollinger_lower: float | None,
    volume_avg_20: float | None,
    vol_annualized_20d: float | None,
    max_drawdown_60d: float | None,
    current_drawdown_60d: float | None,
    return_1d: float | None,
    return_5d: float | None,
    return_20d: float | None,
    return_60d: float | None,
) -> SignalPayload:
    """Calcula o score e sinal de mercado a partir dos indicadores do snapshot."""
    reason_codes = evaluate(
        last_close=last_close,
        last_volume=last_volume,
        sma_20=sma_20,
        sma_50=sma_50,
        ema_20=ema_20,
        rsi_14=rsi_14,
        macd=macd,
        macd_signal=macd_signal,
        bollinger_upper=bollinger_upper,
        bollinger_middle=bollinger_middle,
        bollinger_lower=bollinger_lower,
        volume_avg_20=volume_avg_20,
        vol_annualized_20d=vol_annualized_20d,
        max_drawdown_60d=max_drawdown_60d,
        current_drawdown_60d=current_drawdown_60d,
        return_1d=return_1d,
        return_5d=return_5d,
        return_20d=return_20d,
        return_60d=return_60d,
    )

    pillar_scores = {
        "trend": p.trend_score(reason_codes),
        "momentum": p.momentum_score(reason_codes),
        "volume": p.volume_score(reason_codes),
        "risk": p.risk_score(reason_codes),
        "structure": p.structure_score(reason_codes),
    }

    total = sum(pillar_scores[k] * _WEIGHTS[k] for k in _WEIGHTS)
    total = round(total, 4)

    if total >= _BULLISH_THRESHOLD:
        signal_type = "bullish"
    elif total <= _BEARISH_THRESHOLD:
        signal_type = "bearish"
    else:
        signal_type = "neutral"

    strength = round(abs(total - 50.0) / 50.0, 4)

    return SignalPayload(
        score=total,
        signal_type=signal_type,
        strength=strength,
        scoring_version=SCORING_VERSION,
        reason_codes=reason_codes,
        pillar_scores=pillar_scores,
    )
