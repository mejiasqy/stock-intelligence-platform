from dataclasses import dataclass

import pandas as pd

# RSI: precisa de pelo menos `period + 1` candles para a primeira diferença + EMA inicial.
RSI_MIN = 15

# MACD(12,26,9): EMA26 exige 26 candles; linha de sinal (EMA9 do MACD) exige 9 a mais.
MACD_MIN = 35


def rsi(close: pd.Series, period: int = 14) -> float | None:
    if len(close) < RSI_MIN:
        return None
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    # Wilder's smoothing via ewm alpha = 1/period, adjust=False (recursivo).
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    last_loss = avg_loss.iloc[-1]
    if last_loss == 0:
        return 100.0
    rs = avg_gain.iloc[-1] / last_loss
    return float(100 - (100 / (1 + rs)))


@dataclass(slots=True)
class MACDResult:
    macd: float
    signal: float
    histogram: float


def macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
) -> MACDResult | None:
    if len(close) < MACD_MIN:
        return None
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line
    return MACDResult(
        macd=float(macd_line.iloc[-1]),
        signal=float(signal_line.iloc[-1]),
        histogram=float(histogram.iloc[-1]),
    )
