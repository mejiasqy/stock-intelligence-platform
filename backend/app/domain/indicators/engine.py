"""Motor de cálculo de indicadores técnicos.

CALCULATION_VERSION deve ser incrementado manualmente sempre que houver mudança
em lógica, parâmetros, convenções ou tratamento de dados dos indicadores.
Toda migração de recálculo em dados históricos deve registrar a versão anterior.
"""

from dataclasses import dataclass, field

import pandas as pd

from app.domain.indicators.bands import bollinger
from app.domain.indicators.moving_averages import ema, sma
from app.domain.indicators.oscillators import macd, rsi
from app.domain.indicators.returns import period_return, volume_avg
from app.domain.indicators.risk import annualized_volatility, drawdown_60d

CALCULATION_VERSION = "1.0.0"

# Candles mínimos exigidos por campo — usado para preencher insufficient_fields.
MINIMUMS: dict[str, int] = {
    "return_1d": 2,
    "return_5d": 6,
    "return_20d": 21,
    "return_60d": 61,
    "rsi_14": 15,
    "sma_20": 20,
    "ema_20": 20,
    "bollinger_upper": 20,
    "bollinger_middle": 20,
    "bollinger_lower": 20,
    "vol_annualized_20d": 21,
    "macd": 35,
    "macd_signal": 35,
    "macd_histogram": 35,
    "sma_50": 50,
    "max_drawdown_60d": 60,
    "current_drawdown_60d": 60,
    "volume_avg_20": 20,
}


@dataclass
class SnapshotPayload:
    candles_used: int
    status: str  # ok | partial | insufficient_data
    calculation_version: str

    sma_20: float | None = None
    sma_50: float | None = None
    ema_20: float | None = None
    rsi_14: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None
    bollinger_upper: float | None = None
    bollinger_middle: float | None = None
    bollinger_lower: float | None = None
    volume_avg_20: float | None = None
    vol_annualized_20d: float | None = None
    max_drawdown_60d: float | None = None
    current_drawdown_60d: float | None = None
    return_1d: float | None = None
    return_5d: float | None = None
    return_20d: float | None = None
    return_60d: float | None = None

    # Último candle — necessário para scoring (comparação com médias e volume médio).
    last_close: float | None = None
    last_volume: float | None = None

    # {nome_do_campo: mínimo_requerido} para todos os campos com None.
    insufficient_fields: dict[str, int] = field(default_factory=dict)


def compute(close: pd.Series, volume: pd.Series) -> SnapshotPayload:
    """Calcula o snapshot de indicadores sobre a série completa disponível.

    Recebe as séries em ordem cronológica ascendente.
    Retorna None em cada campo quando o histórico é insuficiente.
    Nunca expõe NaN ou Infinity no resultado.
    """
    n = len(close)

    if n < 2:
        return SnapshotPayload(
            candles_used=n,
            status="insufficient_data",
            calculation_version=CALCULATION_VERSION,
            last_close=float(close.iloc[-1]) if n >= 1 else None,
            last_volume=float(volume.iloc[-1]) if n >= 1 else None,
            insufficient_fields=dict(MINIMUMS),
        )

    macd_res = macd(close)
    boll_res = bollinger(close)
    dd_res = drawdown_60d(close)

    sma_20_v = sma(close, 20)
    sma_50_v = sma(close, 50)
    ema_20_v = ema(close, 20)
    rsi_14_v = rsi(close, 14)
    macd_v = macd_res.macd if macd_res else None
    macd_signal_v = macd_res.signal if macd_res else None
    macd_histogram_v = macd_res.histogram if macd_res else None
    boll_upper_v = boll_res.upper if boll_res else None
    boll_middle_v = boll_res.middle if boll_res else None
    boll_lower_v = boll_res.lower if boll_res else None
    vol_avg_v = volume_avg(volume, 20)
    vol_ann_v = annualized_volatility(close, 20)
    max_dd_v = dd_res.max_drawdown if dd_res else None
    curr_dd_v = dd_res.current_drawdown if dd_res else None
    ret_1d_v = period_return(close, 1)
    ret_5d_v = period_return(close, 5)
    ret_20d_v = period_return(close, 20)
    ret_60d_v = period_return(close, 60)

    computed: dict[str, float | None] = {
        "sma_20": sma_20_v,
        "sma_50": sma_50_v,
        "ema_20": ema_20_v,
        "rsi_14": rsi_14_v,
        "macd": macd_v,
        "macd_signal": macd_signal_v,
        "macd_histogram": macd_histogram_v,
        "bollinger_upper": boll_upper_v,
        "bollinger_middle": boll_middle_v,
        "bollinger_lower": boll_lower_v,
        "volume_avg_20": vol_avg_v,
        "vol_annualized_20d": vol_ann_v,
        "max_drawdown_60d": max_dd_v,
        "current_drawdown_60d": curr_dd_v,
        "return_1d": ret_1d_v,
        "return_5d": ret_5d_v,
        "return_20d": ret_20d_v,
        "return_60d": ret_60d_v,
    }

    insufficient: dict[str, int] = {
        fname: MINIMUMS[fname]
        for fname, val in computed.items()
        if val is None and fname in MINIMUMS
    }

    return SnapshotPayload(
        candles_used=n,
        status="ok" if not insufficient else "partial",
        calculation_version=CALCULATION_VERSION,
        last_close=float(close.iloc[-1]),
        last_volume=float(volume.iloc[-1]),
        sma_20=sma_20_v,
        sma_50=sma_50_v,
        ema_20=ema_20_v,
        rsi_14=rsi_14_v,
        macd=macd_v,
        macd_signal=macd_signal_v,
        macd_histogram=macd_histogram_v,
        bollinger_upper=boll_upper_v,
        bollinger_middle=boll_middle_v,
        bollinger_lower=boll_lower_v,
        volume_avg_20=vol_avg_v,
        vol_annualized_20d=vol_ann_v,
        max_drawdown_60d=max_dd_v,
        current_drawdown_60d=curr_dd_v,
        return_1d=ret_1d_v,
        return_5d=ret_5d_v,
        return_20d=ret_20d_v,
        return_60d=ret_60d_v,
        insufficient_fields=insufficient,
    )
