"""Testes unitários dos indicadores técnicos com fixtures numéricas verificáveis."""

import math

import numpy as np
import pandas as pd
import pytest

from app.domain.indicators.bands import bollinger
from app.domain.indicators.engine import CALCULATION_VERSION, compute
from app.domain.indicators.moving_averages import ema, sma
from app.domain.indicators.oscillators import macd, rsi
from app.domain.indicators.returns import period_return, volume_avg
from app.domain.indicators.risk import annualized_volatility, drawdown_60d

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _series(values: list[float]) -> pd.Series:
    return pd.Series(values, dtype="float64")


def _const(n: int, v: float = 10.0) -> pd.Series:
    return _series([v] * n)


# ---------------------------------------------------------------------------
# SMA
# ---------------------------------------------------------------------------


def test_sma_known_value() -> None:
    s = _series([1.0, 2.0, 3.0, 4.0, 5.0])
    assert sma(s, 3) == pytest.approx(4.0)  # mean(3,4,5)


def test_sma_insufficient_returns_none() -> None:
    assert sma(_series([1.0, 2.0]), 3) is None


def test_sma_full_period() -> None:
    s = _series([2.0, 4.0, 6.0])
    assert sma(s, 3) == pytest.approx(4.0)


# ---------------------------------------------------------------------------
# EMA — adjust=False (recursivo)
# ---------------------------------------------------------------------------


def test_ema_constant_series_equals_constant() -> None:
    """EMA de série constante deve ser igual ao valor constante."""
    s = _const(30, 5.0)
    result = ema(s, 20)
    assert result == pytest.approx(5.0, rel=1e-6)


def test_ema_insufficient_returns_none() -> None:
    assert ema(_series([1.0] * 10), 20) is None


def test_ema_adjust_false_convention() -> None:
    """Verifica EMA com adjust=False contra cálculo manual de 3 períodos."""
    # EMA(3) com adjust=False: alpha = 2/(3+1) = 0.5
    # t0: 10, t1: 0.5*12 + 0.5*10 = 11, t2: 0.5*8 + 0.5*11 = 9.5
    s = _series([10.0, 12.0, 8.0])
    result = ema(s, 3)
    assert result == pytest.approx(9.5, rel=1e-6)


# ---------------------------------------------------------------------------
# RSI
# ---------------------------------------------------------------------------


def test_rsi_constant_series() -> None:
    """RSI de série constante (sem ganhos nem perdas) deve ser 100 ou 0."""
    # diff = 0, avg_loss = 0 → RSI = 100 (sem perdas)
    s = _const(20, 10.0)
    result = rsi(s, 14)
    assert result == pytest.approx(100.0)


def test_rsi_insufficient_returns_none() -> None:
    assert rsi(_series([1.0] * 10), 14) is None


def test_rsi_range() -> None:
    """RSI deve sempre estar entre 0 e 100."""
    rng = np.random.default_rng(42)
    values = list(rng.uniform(10, 100, 50))
    result = rsi(_series(values), 14)
    assert result is not None
    assert 0.0 <= result <= 100.0


# ---------------------------------------------------------------------------
# MACD
# ---------------------------------------------------------------------------


def test_macd_constant_series_histogram_zero() -> None:
    """MACD de série constante deve ter histograma próximo de zero."""
    s = _const(50, 10.0)
    result = macd(s)
    assert result is not None
    assert result.histogram == pytest.approx(0.0, abs=1e-8)


def test_macd_insufficient_returns_none() -> None:
    assert macd(_series([1.0] * 20)) is None


def test_macd_fields_present() -> None:
    s = _const(50, 10.0)
    result = macd(s)
    assert result is not None
    assert hasattr(result, "macd")
    assert hasattr(result, "signal")
    assert hasattr(result, "histogram")


# ---------------------------------------------------------------------------
# Bollinger Bands
# ---------------------------------------------------------------------------


def test_bollinger_constant_series_zero_std() -> None:
    """Série constante → std=0 → upper=middle=lower."""
    s = _const(25, 10.0)
    result = bollinger(s)
    assert result is not None
    assert result.upper == pytest.approx(result.middle)
    assert result.lower == pytest.approx(result.middle)


def test_bollinger_insufficient_returns_none() -> None:
    assert bollinger(_series([1.0] * 10)) is None


def test_bollinger_ordering() -> None:
    """upper ≥ middle ≥ lower para série com variação."""
    rng = np.random.default_rng(42)
    s = _series(list(rng.uniform(9, 11, 25)))
    result = bollinger(s)
    assert result is not None
    assert result.upper >= result.middle >= result.lower


# ---------------------------------------------------------------------------
# Volatilidade anualizada
# ---------------------------------------------------------------------------


def test_annualized_volatility_constant_series_zero() -> None:
    """Série constante → retornos = 0 → volatilidade = 0."""
    s = _const(30, 10.0)
    result = annualized_volatility(s)
    assert result == pytest.approx(0.0, abs=1e-8)


def test_annualized_volatility_insufficient_returns_none() -> None:
    assert annualized_volatility(_series([1.0] * 15)) is None


def test_annualized_volatility_uses_sqrt252() -> None:
    """Verifica a fórmula: std_daily(ddof=1) × sqrt(252)."""
    rng = np.random.default_rng(7)
    prices = pd.Series(100 * np.cumprod(1 + rng.normal(0, 0.01, 30)))
    returns = prices.pct_change()
    expected = float(returns.rolling(20).std(ddof=1).iloc[-1] * np.sqrt(252))
    result = annualized_volatility(prices, 20)
    assert result == pytest.approx(expected, rel=1e-9)


# ---------------------------------------------------------------------------
# Drawdown
# ---------------------------------------------------------------------------


def test_drawdown_constant_series_zero() -> None:
    s = _const(60, 10.0)
    result = drawdown_60d(s)
    assert result is not None
    assert result.max_drawdown == pytest.approx(0.0, abs=1e-8)
    assert result.current_drawdown == pytest.approx(0.0, abs=1e-8)


def test_drawdown_insufficient_returns_none() -> None:
    assert drawdown_60d(_series([1.0] * 30)) is None


def test_drawdown_monotone_decline() -> None:
    """Queda monotônica de 100→41 (60 candles) → max_drawdown próximo de -0.59."""
    prices = list(range(100, 40, -1))  # 60 elementos: 100, 99, ..., 41
    assert len(prices) == 60
    s = _series(prices)
    result = drawdown_60d(s)
    assert result is not None
    assert result.max_drawdown < 0
    # Pico = 100, mínimo = 41 → drawdown = (41-100)/100 = -0.59
    assert result.max_drawdown == pytest.approx(-0.59, rel=0.02)


# ---------------------------------------------------------------------------
# Retornos por período
# ---------------------------------------------------------------------------


def test_period_return_1d() -> None:
    s = _series([100.0, 110.0])
    assert period_return(s, 1) == pytest.approx(0.1)


def test_period_return_insufficient() -> None:
    assert period_return(_series([100.0]), 1) is None


def test_period_return_negative() -> None:
    s = _series([200.0, 100.0])
    assert period_return(s, 1) == pytest.approx(-0.5)


# ---------------------------------------------------------------------------
# Volume médio
# ---------------------------------------------------------------------------


def test_volume_avg_known() -> None:
    v = _series([1000.0] * 10 + [2000.0] * 10)
    assert volume_avg(v, 20) == pytest.approx(1500.0)


def test_volume_avg_insufficient() -> None:
    assert volume_avg(_series([1000.0] * 5), 20) is None


# ---------------------------------------------------------------------------
# engine.compute — estados e campos
# ---------------------------------------------------------------------------


def test_compute_insufficient_data_below_2() -> None:
    result = compute(_series([10.0]), _series([1000.0]))
    assert result.status == "insufficient_data"
    assert result.sma_20 is None


def test_compute_partial_status_few_candles() -> None:
    """Com 10 candles, vários indicadores serão None → status=partial."""
    close = _series([10.0 + i * 0.1 for i in range(10)])
    volume = _series([1000.0] * 10)
    result = compute(close, volume)
    assert result.status == "partial"
    assert result.sma_20 is None
    assert result.return_1d is not None


def test_compute_ok_status_sufficient_candles() -> None:
    """Com 70 candles, todos os indicadores devem estar disponíveis → status=ok."""
    rng = np.random.default_rng(1)
    prices = pd.Series(50 * np.cumprod(1 + rng.normal(0.0003, 0.015, 70)))
    volumes = pd.Series(rng.integers(500_000, 2_000_000, 70).astype(float))
    result = compute(prices, volumes)
    assert result.status == "ok"
    assert result.insufficient_fields == {}
    assert result.sma_20 is not None
    assert result.sma_50 is not None
    assert result.ema_20 is not None
    assert result.rsi_14 is not None
    assert result.macd is not None
    assert result.bollinger_upper is not None
    assert result.vol_annualized_20d is not None
    assert result.max_drawdown_60d is not None
    assert result.return_60d is not None


def test_compute_no_nan_exposed() -> None:
    """Nenhum campo numérico do resultado pode ser NaN ou Infinity."""
    rng = np.random.default_rng(99)
    prices = pd.Series(10 * np.cumprod(1 + rng.normal(0, 0.02, 100)))
    volumes = pd.Series(rng.integers(100_000, 1_000_000, 100).astype(float))
    result = compute(prices, volumes)
    numeric_fields = [
        result.sma_20,
        result.sma_50,
        result.ema_20,
        result.rsi_14,
        result.macd,
        result.macd_signal,
        result.macd_histogram,
        result.bollinger_upper,
        result.bollinger_middle,
        result.bollinger_lower,
        result.volume_avg_20,
        result.vol_annualized_20d,
        result.max_drawdown_60d,
        result.current_drawdown_60d,
        result.return_1d,
        result.return_5d,
        result.return_20d,
        result.return_60d,
    ]
    for val in numeric_fields:
        if val is not None:
            assert not math.isnan(val), f"NaN encontrado: {val}"
            assert not math.isinf(val), f"Infinity encontrado: {val}"


def test_compute_calculation_version() -> None:
    close = _const(10, 10.0)
    result = compute(close, _const(10, 1000.0))
    assert result.calculation_version == CALCULATION_VERSION


def test_compute_insufficient_fields_populated_correctly() -> None:
    """insufficient_fields deve listar campos ausentes com seus mínimos."""
    close = _series([10.0 + i for i in range(10)])
    result = compute(close, _series([1000.0] * 10))
    assert "sma_20" in result.insufficient_fields
    assert result.insufficient_fields["sma_20"] == 20
    assert "return_1d" not in result.insufficient_fields  # disponível com 10 candles
