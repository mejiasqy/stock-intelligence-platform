"""Protocolo de estratégia e implementação SMA crossover 20/50."""

from typing import Protocol

import pandas as pd


class Strategy(Protocol):
    """Interface mínima que toda estratégia de backtest deve satisfazer."""

    strategy_name: str
    strategy_version: str

    def min_bars_required(self) -> int:
        """Número mínimo de candles para gerar o primeiro sinal válido."""
        ...

    def parameters(self) -> dict:
        """Parâmetros imutáveis da estratégia para persistência no snapshot."""
        ...

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Gera sinais sobre o DataFrame completo sem look-ahead.

        df: colunas open, high, low, close, volume; índice = timestamps.
        Retorna Series com valores 'buy', 'sell' ou None, mesmo índice que df.
        Usa apenas rolling windows — nunca dados futuros.
        """
        ...


class SMACrossover:
    """Estratégia SMA crossover (default: rápida=20, lenta=50), long-only.

    Entrada: SMA rápida cruza acima da SMA lenta no fechamento do bar t.
    Saída:   SMA rápida cruza abaixo da SMA lenta no fechamento do bar t.
    Execução: open do bar t+1 (sem look-ahead).
    """

    strategy_name = "sma_crossover"
    strategy_version = "1.0.0"

    def __init__(self, fast_period: int = 20, slow_period: int = 50) -> None:
        if fast_period >= slow_period:
            raise ValueError("fast_period deve ser menor que slow_period")
        self.fast_period = fast_period
        self.slow_period = slow_period

    def min_bars_required(self) -> int:
        return self.slow_period + 1

    def parameters(self) -> dict:
        return {"fast_period": self.fast_period, "slow_period": self.slow_period}

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"]
        fast = close.rolling(self.fast_period).mean()
        slow = close.rolling(self.slow_period).mean()

        fast_prev = fast.shift(1)
        slow_prev = slow.shift(1)

        signals: pd.Series = pd.Series(None, index=df.index, dtype=object)
        signals.loc[(fast_prev <= slow_prev) & (fast > slow)] = "buy"
        signals.loc[(fast_prev >= slow_prev) & (fast < slow)] = "sell"
        return signals


def get_strategy(name: str, params: dict | None = None) -> SMACrossover:
    """Retorna a estratégia pelo nome com parâmetros opcionais."""
    p = params or {}
    if name == "sma_crossover":
        return SMACrossover(
            fast_period=p.get("fast_period", 20),
            slow_period=p.get("slow_period", 50),
        )
    raise ValueError(f"Estratégia desconhecida: {name!r}")
