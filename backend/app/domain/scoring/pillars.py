"""Cálculo de score por pilar a partir dos reason_codes avaliados.

Cada pilar retorna um score de 0.0 a 100.0.
Cada código do pilar tem peso igual dentro do pilar.
"""


def _equal_weight_score(codes: list[str], results: dict[str, bool]) -> float:
    n = len(codes)
    if n == 0:
        return 0.0
    triggered = sum(1 for c in codes if results.get(c, False))
    return round(triggered / n * 100.0, 4)


def trend_score(results: dict[str, bool]) -> float:
    codes = [
        "price_above_sma_20",
        "price_above_sma_50",
        "ema_above_sma_20",
        "return_20d_positive",
        "return_60d_positive",
    ]
    return _equal_weight_score(codes, results)


def momentum_score(results: dict[str, bool]) -> float:
    codes = [
        "macd_positive",
        "macd_above_signal",
        "return_1d_positive",
        "return_5d_positive",
        "rsi_in_bullish_range",
    ]
    return _equal_weight_score(codes, results)


def volume_score(results: dict[str, bool]) -> float:
    # volume_surge implica volume_above_avg; surge vale 100, apenas avg vale 60.
    if results.get("volume_surge", False):
        return 100.0
    if results.get("volume_above_avg", False):
        return 60.0
    return 0.0


def risk_score(results: dict[str, bool]) -> float:
    codes = [
        "volatility_contained",
        "current_drawdown_mild",
        "max_drawdown_acceptable",
    ]
    return _equal_weight_score(codes, results)


def structure_score(results: dict[str, bool]) -> float:
    codes = [
        "price_above_bollinger_lower",
        "price_at_or_above_mid_band",
        "sma_20_above_sma_50",
        "return_5d_outpacing_20d",
        "price_below_bollinger_upper",
    ]
    return _equal_weight_score(codes, results)
