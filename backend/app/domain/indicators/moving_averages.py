import pandas as pd


def sma(close: pd.Series, period: int) -> float | None:
    if len(close) < period:
        return None
    return float(close.rolling(period).mean().iloc[-1])


def ema(close: pd.Series, period: int) -> float | None:
    """EMA com adjust=False (cálculo recursivo, equivalente à convenção de mercado)."""
    if len(close) < period:
        return None
    return float(close.ewm(span=period, adjust=False).mean().iloc[-1])
