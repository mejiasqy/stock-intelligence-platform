import pandas as pd


def period_return(close: pd.Series, n: int) -> float | None:
    """Retorno simples entre o candle mais recente e n candles atrás.

    Requer n+1 candles (o candle base + n de distância).
    """
    if len(close) < n + 1:
        return None
    return float((close.iloc[-1] / close.iloc[-(n + 1)]) - 1)


def volume_avg(volume: pd.Series, period: int = 20) -> float | None:
    if len(volume) < period:
        return None
    return float(volume.iloc[-period:].mean())
