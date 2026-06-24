from dataclasses import dataclass

import pandas as pd

BOLLINGER_MIN = 20


@dataclass(slots=True)
class BollingerResult:
    upper: float
    middle: float
    lower: float


def bollinger(close: pd.Series, period: int = 20, num_std: float = 2.0) -> BollingerResult | None:
    if len(close) < BOLLINGER_MIN:
        return None
    middle = close.rolling(period).mean()
    std = close.rolling(period).std(ddof=1)
    upper = middle + num_std * std
    lower = middle - num_std * std
    return BollingerResult(
        upper=float(upper.iloc[-1]),
        middle=float(middle.iloc[-1]),
        lower=float(lower.iloc[-1]),
    )
