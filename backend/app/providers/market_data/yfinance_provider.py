from datetime import date, timedelta

import pandas as pd
import yfinance as yf


class YFinanceProvider:
    """Adaptador yfinance que implementa o protocolo MarketDataProvider."""

    def fetch_ohlcv(self, symbol: str, days: int) -> pd.DataFrame:
        end = date.today()
        start = end - timedelta(days=days)

        ticker = yf.Ticker(symbol)
        raw = ticker.history(start=start.isoformat(), end=end.isoformat(), auto_adjust=True)

        if raw.empty:
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

        df = raw.reset_index()[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()
        df.columns = pd.Index(["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df["volume"] = df["volume"].fillna(0).astype("int64")
        return df
