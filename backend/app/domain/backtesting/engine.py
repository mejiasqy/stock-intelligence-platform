"""Motor de backtesting walk-forward — sem look-ahead bias.

BACKTEST_ENGINE_VERSION deve ser incrementado manualmente a cada mudança de
lógica do motor (ordem de execução, cálculo de custos, métricas).
Todo run persiste engine_version para garantir reprodutibilidade.
"""

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from app.domain.backtesting.metrics import (
    BacktestMetrics,
    compute_benchmark,
    compute_metrics,
)
from app.domain.backtesting.strategy import Strategy

BACKTEST_ENGINE_VERSION = "1.0.0"


@dataclass
class BacktestParams:
    initial_capital: float
    transaction_cost_bps: int
    slippage_bps: int
    risk_free_rate_pct: float


@dataclass
class TradeRecord:
    entry_timestamp: Any  # pd.Timestamp
    exit_timestamp: Any
    entry_price: float  # open do bar de execução (sem slippage)
    exit_price: float  # open/close do bar de saída (sem slippage)
    executed_entry_price: float  # com slippage
    executed_exit_price: float
    quantity: int
    gross_pnl: float  # sem custos
    net_pnl: float  # após custos e slippage
    fees_paid: float
    reason_entry: str
    reason_exit: str


@dataclass
class BacktestResult:
    status: str  # "completed" | "insufficient_data"
    params: BacktestParams
    strategy_name: str
    strategy_version: str
    data_start: Any | None  # pd.Timestamp
    data_end: Any | None
    trades: list[TradeRecord] = field(default_factory=list)
    equity_curve: list[dict] = field(default_factory=list)
    metrics: BacktestMetrics | None = None
    benchmark_return_pct: float | None = None


def _entry_cost(exec_price: float, qty: int, cost_bps: int) -> float:
    return exec_price * qty * cost_bps / 10_000.0


def run_backtest(
    df: pd.DataFrame,
    strategy: Strategy,
    params: BacktestParams,
) -> BacktestResult:
    """Executa o backtest walk-forward sobre o DataFrame.

    df: colunas open, high, low, close, volume; índice DatetimeIndex cronológico.
    Sinal calculado no fechamento do bar t → executado no open do bar t+1.
    Posição forçada a fechar no close do último bar se ainda aberta ao final.
    """
    data_start = df.index[0] if len(df) > 0 else None
    data_end = df.index[-1] if len(df) > 0 else None

    if len(df) < strategy.min_bars_required():
        return BacktestResult(
            status="insufficient_data",
            params=params,
            strategy_name=strategy.strategy_name,
            strategy_version=strategy.strategy_version,
            data_start=data_start,
            data_end=data_end,
        )

    signals = strategy.generate_signals(df)

    capital = float(params.initial_capital)
    position = 0
    entry_exec_price = 0.0
    entry_raw_price = 0.0
    entry_ts: Any = None
    entry_fees = 0.0

    trades: list[TradeRecord] = []
    equity_curve: list[dict] = []
    days_in_position = 0
    pending_signal: str | None = None

    for i in range(len(df)):
        row = df.iloc[i]
        ts = df.index[i]
        open_price = float(row["open"])

        # ── Executa sinal do bar anterior no open deste bar ──
        if pending_signal == "buy" and position == 0:
            exec_price = open_price * (1.0 + params.slippage_bps / 10_000.0)
            cost_factor = 1.0 + params.transaction_cost_bps / 10_000.0
            qty = int(capital / (exec_price * cost_factor))
            if qty > 0:
                fees = _entry_cost(exec_price, qty, params.transaction_cost_bps)
                capital -= exec_price * qty + fees
                position = qty
                entry_exec_price = exec_price
                entry_raw_price = open_price
                entry_ts = ts
                entry_fees = fees

        elif pending_signal == "sell" and position > 0:
            exec_price = open_price * (1.0 - params.slippage_bps / 10_000.0)
            fees = _entry_cost(exec_price, position, params.transaction_cost_bps)
            proceeds = exec_price * position - fees
            capital += proceeds

            gross = (exec_price - entry_exec_price) * position
            net = proceeds - (entry_exec_price * position + entry_fees)

            trades.append(
                TradeRecord(
                    entry_timestamp=entry_ts,
                    exit_timestamp=ts,
                    entry_price=entry_raw_price,
                    exit_price=open_price,
                    executed_entry_price=entry_exec_price,
                    executed_exit_price=exec_price,
                    quantity=position,
                    gross_pnl=gross,
                    net_pnl=net,
                    fees_paid=entry_fees + fees,
                    reason_entry=f"{strategy.strategy_name}_buy",
                    reason_exit=f"{strategy.strategy_name}_sell",
                )
            )
            position = 0

        # ── Contabiliza exposição e gera equity mark-to-market ──
        if position > 0:
            days_in_position += 1

        close_price = float(row["close"])
        equity = capital + position * close_price
        date_str = ts.date().isoformat() if hasattr(ts, "date") else str(ts)
        equity_curve.append({"date": date_str, "equity": round(equity, 2)})

        # ── Sinal do fechamento deste bar → executado no próximo open ──
        pending_signal = signals.iloc[i]

    # ── Fecha posição aberta no close do último bar (end of period) ──
    if position > 0:
        last_row = df.iloc[-1]
        last_ts = df.index[-1]
        close_price = float(last_row["close"])
        exec_price = close_price * (1.0 - params.slippage_bps / 10_000.0)
        fees = _entry_cost(exec_price, position, params.transaction_cost_bps)
        proceeds = exec_price * position - fees
        capital += proceeds

        gross = (exec_price - entry_exec_price) * position
        net = proceeds - (entry_exec_price * position + entry_fees)

        trades.append(
            TradeRecord(
                entry_timestamp=entry_ts,
                exit_timestamp=last_ts,
                entry_price=entry_raw_price,
                exit_price=close_price,
                executed_entry_price=entry_exec_price,
                executed_exit_price=exec_price,
                quantity=position,
                gross_pnl=gross,
                net_pnl=net,
                fees_paid=entry_fees + fees,
                reason_entry=f"{strategy.strategy_name}_buy",
                reason_exit="end_of_period",
            )
        )
        # Atualiza último ponto da curva de equity com o capital real
        equity_curve[-1]["equity"] = round(capital, 2)
        position = 0

    net_pnls = [t.net_pnl for t in trades]
    metrics = compute_metrics(
        equity_curve=equity_curve,
        net_pnls=net_pnls,
        days_in_position=days_in_position,
        initial_capital=float(params.initial_capital),
        risk_free_rate_pct=float(params.risk_free_rate_pct),
    )
    benchmark = compute_benchmark(
        df=df,
        initial_capital=float(params.initial_capital),
        transaction_cost_bps=params.transaction_cost_bps,
        slippage_bps=params.slippage_bps,
    )

    return BacktestResult(
        status="completed",
        params=params,
        strategy_name=strategy.strategy_name,
        strategy_version=strategy.strategy_version,
        data_start=data_start,
        data_end=data_end,
        trades=trades,
        equity_curve=equity_curve,
        metrics=metrics,
        benchmark_return_pct=benchmark,
    )
