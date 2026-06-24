from dataclasses import dataclass

import numpy as np
import pandas as pd

# Volatilidade rolling 20 sobre retornos — precisa de 21 candles (20 retornos).
VOL_MIN = 21
DRAWDOWN_MIN = 60


def annualized_volatility(close: pd.Series, period: int = 20) -> float | None:
    """Desvio-padrão móvel (ddof=1) dos retornos percentuais diários × sqrt(252)."""
    if len(close) < VOL_MIN:
        return None
    returns = close.pct_change()
    vol = returns.rolling(period).std(ddof=1).iloc[-1]
    return float(vol * np.sqrt(252))


@dataclass(slots=True)
class DrawdownResult:
    max_drawdown: float
    current_drawdown: float


def drawdown_60d(close: pd.Series) -> DrawdownResult | None:
    if len(close) < DRAWDOWN_MIN:
        return None
    window = close.iloc[-60:]
    peak = window.expanding().max()
    dd = (window - peak) / peak
    return DrawdownResult(
        max_drawdown=float(dd.min()),
        current_drawdown=float(dd.iloc[-1]),
    )
