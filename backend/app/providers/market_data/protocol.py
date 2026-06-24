from datetime import date
from typing import Protocol

import pandas as pd


class OHLCVRow(Protocol):
    """Contrato mínimo de uma linha OHLCV normalizada."""

    timestamp: date
    open: float
    high: float
    low: float
    close: float
    volume: int


class MarketDataProvider(Protocol):
    def fetch_ohlcv(self, symbol: str, days: int) -> pd.DataFrame:
        """Retorna DataFrame com colunas: timestamp, open, high, low, close, volume."""
        ...
