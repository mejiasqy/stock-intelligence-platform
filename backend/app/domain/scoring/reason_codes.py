"""Avaliação dos reason_codes sobre um snapshot de indicadores.

Cada código é uma condição binária (True/False). True significa que o critério
bullish foi atendido; False significa que não foi atendido ou dado insuficiente.
Cada código pertence a um pilar e contribui com pontos ao score desse pilar.
"""

from dataclasses import dataclass
from typing import Literal

Pillar = Literal["trend", "momentum", "volume", "risk", "structure"]


@dataclass(frozen=True)
class ReasonCodeDef:
    code: str
    pillar: Pillar
    description: str


REASON_CODE_DEFS: list[ReasonCodeDef] = [
    # Tendência
    ReasonCodeDef("price_above_sma_20", "trend", "Preço acima da SMA de 20 períodos"),
    ReasonCodeDef("price_above_sma_50", "trend", "Preço acima da SMA de 50 períodos"),
    ReasonCodeDef("ema_above_sma_20", "trend", "EMA 20 acima da SMA 20 (momentum de curto prazo)"),
    ReasonCodeDef("return_20d_positive", "trend", "Retorno dos últimos 20 dias positivo"),
    ReasonCodeDef("return_60d_positive", "trend", "Retorno dos últimos 60 dias positivo"),
    # Momentum
    ReasonCodeDef("macd_positive", "momentum", "MACD acima de zero"),
    ReasonCodeDef("macd_above_signal", "momentum", "MACD acima da linha de sinal"),
    ReasonCodeDef("return_1d_positive", "momentum", "Retorno diário positivo"),
    ReasonCodeDef("return_5d_positive", "momentum", "Retorno semanal positivo"),
    ReasonCodeDef("rsi_in_bullish_range", "momentum", "RSI em zona saudável (40–70)"),
    # Volume
    ReasonCodeDef("volume_above_avg", "volume", "Volume acima da média de 20 períodos"),
    ReasonCodeDef("volume_surge", "volume", "Volume acima de 1,5× a média (surge)"),
    # Risco
    ReasonCodeDef("volatility_contained", "risk", "Volatilidade anualizada abaixo de 40%"),
    ReasonCodeDef("current_drawdown_mild", "risk", "Drawdown atual inferior a 15%"),
    ReasonCodeDef("max_drawdown_acceptable", "risk", "Drawdown máximo em 60d inferior a 25%"),
    # Estrutura
    ReasonCodeDef(
        "price_above_bollinger_lower", "structure", "Preço acima da banda inferior de Bollinger"
    ),
    ReasonCodeDef("price_at_or_above_mid_band", "structure", "Preço na banda média ou acima"),
    ReasonCodeDef(
        "sma_20_above_sma_50", "structure", "SMA 20 acima da SMA 50 (alinhamento estrutural)"
    ),
    ReasonCodeDef(
        "return_5d_outpacing_20d",
        "structure",
        "Retorno de 5d superior ao de 20d (aceleração)",
    ),
    ReasonCodeDef(
        "price_below_bollinger_upper",
        "structure",
        "Preço abaixo da banda superior (não sobrecomprado)",
    ),
]

REASON_CODES_BY_PILLAR: dict[Pillar, list[str]] = {
    "trend": [],
    "momentum": [],
    "volume": [],
    "risk": [],
    "structure": [],
}
for _def in REASON_CODE_DEFS:
    REASON_CODES_BY_PILLAR[_def.pillar].append(_def.code)


def evaluate(
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
) -> dict[str, bool]:
    """Avalia todos os reason_codes e retorna um dict {code: bool}."""
    c = last_close
    v = last_volume

    return {
        # Tendência
        "price_above_sma_20": c is not None and sma_20 is not None and c > sma_20,
        "price_above_sma_50": c is not None and sma_50 is not None and c > sma_50,
        "ema_above_sma_20": ema_20 is not None and sma_20 is not None and ema_20 > sma_20,
        "return_20d_positive": return_20d is not None and return_20d > 0,
        "return_60d_positive": return_60d is not None and return_60d > 0,
        # Momentum
        "macd_positive": macd is not None and macd > 0,
        "macd_above_signal": macd is not None and macd_signal is not None and macd > macd_signal,
        "return_1d_positive": return_1d is not None and return_1d > 0,
        "return_5d_positive": return_5d is not None and return_5d > 0,
        "rsi_in_bullish_range": rsi_14 is not None and 40.0 <= rsi_14 <= 70.0,
        # Volume
        "volume_above_avg": v is not None and volume_avg_20 is not None and v > volume_avg_20,
        "volume_surge": v is not None and volume_avg_20 is not None and v > 1.5 * volume_avg_20,
        # Risco
        "volatility_contained": vol_annualized_20d is not None and vol_annualized_20d < 0.40,
        "current_drawdown_mild": current_drawdown_60d is not None and current_drawdown_60d > -0.15,
        "max_drawdown_acceptable": max_drawdown_60d is not None and max_drawdown_60d > -0.25,
        # Estrutura
        "price_above_bollinger_lower": (
            c is not None and bollinger_lower is not None and c > bollinger_lower
        ),
        "price_at_or_above_mid_band": (
            c is not None and bollinger_middle is not None and c >= bollinger_middle
        ),
        "sma_20_above_sma_50": (sma_20 is not None and sma_50 is not None and sma_20 > sma_50),
        "return_5d_outpacing_20d": (
            return_5d is not None and return_20d is not None and return_5d > return_20d
        ),
        "price_below_bollinger_upper": (
            c is not None and bollinger_upper is not None and c < bollinger_upper
        ),
    }
