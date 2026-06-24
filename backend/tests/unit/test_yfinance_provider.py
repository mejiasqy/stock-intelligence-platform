"""Testes unitários do YFinanceProvider — transformação e limpeza do DataFrame."""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

from app.providers.market_data.yfinance_provider import YFinanceProvider


def _make_raw_df(**overrides: object) -> pd.DataFrame:
    """Monta um DataFrame no formato que yfinance.Ticker.history() retorna."""
    base: dict[str, object] = {
        "Date": pd.to_datetime(["2024-01-04", "2024-01-02", "2024-01-03"]),
        "Open": [32.0, 30.0, 31.0],
        "High": [33.0, 31.0, 32.0],
        "Low": [31.0, 29.0, 30.0],
        "Close": [32.5, 30.5, 31.5],
        "Volume": [900000, 1000000, 1200000],
    }
    base.update(overrides)
    df = pd.DataFrame(base)
    df = df.set_index("Date")
    return df


def _fetch_with_mock(raw_df: pd.DataFrame) -> pd.DataFrame:
    provider = YFinanceProvider()
    with patch("app.providers.market_data.yfinance_provider.yf.Ticker") as mock_ticker_cls:
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = raw_df
        mock_ticker_cls.return_value = mock_ticker
        return provider.fetch_ohlcv("TEST3.SA", 30)


def test_fetch_ohlcv_sorted_ascending() -> None:
    """DataFrame fora de ordem deve ser retornado ordenado por timestamp ascendente."""
    result = _fetch_with_mock(_make_raw_df())
    timestamps = result["timestamp"].tolist()
    assert timestamps == sorted(timestamps), "timestamps devem estar em ordem crescente"


def test_fetch_ohlcv_drops_row_with_nan_open() -> None:
    """Linha com NaN em 'open' deve ser removida."""
    raw = _make_raw_df(Open=[np.nan, 30.0, 31.0])
    result = _fetch_with_mock(raw)
    assert len(result) == 2
    assert not result["open"].isna().any()


def test_fetch_ohlcv_drops_row_with_nan_close() -> None:
    """Linha com NaN em 'close' deve ser removida."""
    raw = _make_raw_df(Close=[np.nan, 30.5, 31.5])
    result = _fetch_with_mock(raw)
    assert len(result) == 2


def test_fetch_ohlcv_drops_row_with_nan_high_or_low() -> None:
    """Linhas com NaN em 'high' ou 'low' também devem ser removidas."""
    raw = _make_raw_df(High=[np.nan, 31.0, 32.0], Low=[31.0, np.nan, 30.0])
    result = _fetch_with_mock(raw)
    assert len(result) == 1


def test_fetch_ohlcv_keeps_zero_volume_when_ohlc_valid() -> None:
    """Volume nulo com OHLC válido deve ser mantido com volume=0.

    _make_raw_df coloca datas [2024-01-04, 2024-01-02, 2024-01-03].
    Após sort ascendente: [2024-01-02, 2024-01-03, 2024-01-04].
    Volume=[nan, 1000000, 1200000] corresponde originalmente às datas nessa ordem,
    portanto nan pertence a 2024-01-04 → iloc[-1] após sort.
    """
    raw = _make_raw_df(Volume=[np.nan, 1000000, 1200000])
    result = _fetch_with_mock(raw)
    assert len(result) == 3
    assert result["volume"].iloc[-1] == 0  # 2024-01-04 tinha volume NaN
    assert result["volume"].dtype == "int64"


def test_fetch_ohlcv_empty_ticker_returns_empty_df() -> None:
    """Ticker sem dados deve retornar DataFrame vazio com colunas corretas."""
    provider = YFinanceProvider()
    with patch("app.providers.market_data.yfinance_provider.yf.Ticker") as mock_ticker_cls:
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_ticker_cls.return_value = mock_ticker
        result = provider.fetch_ohlcv("NOTFOUND.SA", 30)
    assert result.empty
    assert list(result.columns) == ["timestamp", "open", "high", "low", "close", "volume"]


def test_fetch_ohlcv_no_nan_in_result() -> None:
    """O DataFrame retornado não deve conter NaN em nenhuma coluna OHLC."""
    result = _fetch_with_mock(_make_raw_df())
    for col in ["open", "high", "low", "close"]:
        assert not result[col].isna().any(), f"coluna '{col}' não deve ter NaN"
