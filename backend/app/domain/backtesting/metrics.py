"""Cálculo de métricas de desempenho do backtest."""

import math
from dataclasses import dataclass

import pandas as pd


@dataclass
class BacktestMetrics:
    total_return_pct: float
    annualized_return_pct: float | None
    volatility_pct: float | None
    sharpe_ratio: float | None
    max_drawdown_pct: float
    win_rate_pct: float | None
    profit_factor: float | None  # None = sem trades perdedores
    trade_count: int
    exposure_pct: float | None


def compute_metrics(
    equity_curve: list[dict],
    net_pnls: list[float],
    days_in_position: int,
    initial_capital: float,
    risk_free_rate_pct: float,
) -> BacktestMetrics:
    """Calcula métricas a partir da curva de equity e lista de net_pnls dos trades.

    equity_curve: [{"date": str, "equity": float}, ...]  ordem cronológica.
    net_pnls: net_pnl de cada trade fechado.
    days_in_position: total de dias (bars) em que havia posição aberta.
    """
    n = len(equity_curve)
    if n == 0:
        return BacktestMetrics(
            total_return_pct=0.0,
            annualized_return_pct=None,
            volatility_pct=None,
            sharpe_ratio=None,
            max_drawdown_pct=0.0,
            win_rate_pct=None,
            profit_factor=None,
            trade_count=len(net_pnls),
            exposure_pct=None,
        )

    equities = pd.Series([e["equity"] for e in equity_curve], dtype="float64")
    final = float(equities.iloc[-1])

    total_return = (final - initial_capital) / initial_capital * 100

    ann_return: float | None = None
    if n > 1:
        ratio = final / initial_capital
        if ratio > 0:
            ann_return = ((ratio) ** (252.0 / n) - 1.0) * 100

    # Volatilidade e Sharpe a partir dos retornos diários (ddof=1, consistente com Sprint 2)
    daily_rets = equities.pct_change().dropna()
    volatility: float | None = None
    sharpe: float | None = None
    if len(daily_rets) >= 2:
        std = float(daily_rets.std(ddof=1))
        if std > 0:
            volatility = std * math.sqrt(252) * 100
            rf_daily = (1.0 + risk_free_rate_pct / 100.0) ** (1.0 / 252.0) - 1.0
            mean_excess = float((daily_rets - rf_daily).mean())
            sharpe = (mean_excess / std) * math.sqrt(252)

    # Maximum drawdown da curva de equity
    peak = equities.cummax()
    drawdown = (equities - peak) / peak
    max_dd = float(drawdown.min()) * 100  # valor negativo

    # Métricas de trades
    trade_count = len(net_pnls)
    win_rate: float | None = None
    profit_factor: float | None = None
    if trade_count > 0:
        winners = sum(1 for p in net_pnls if p > 0)
        win_rate = winners / trade_count * 100
        gains = sum(p for p in net_pnls if p > 0)
        losses = sum(p for p in net_pnls if p < 0)
        profit_factor = gains / abs(losses) if losses < 0 else None

    exposure: float | None = days_in_position / n * 100 if n > 0 else None

    return BacktestMetrics(
        total_return_pct=total_return,
        annualized_return_pct=ann_return,
        volatility_pct=volatility,
        sharpe_ratio=sharpe,
        max_drawdown_pct=max_dd,
        win_rate_pct=win_rate,
        profit_factor=profit_factor,
        trade_count=trade_count,
        exposure_pct=exposure,
    )


def compute_benchmark(
    df: pd.DataFrame,
    initial_capital: float,
    transaction_cost_bps: int,
    slippage_bps: int,
) -> float:
    """Retorno percentual de uma estratégia buy-and-hold com os mesmos custos."""
    if len(df) < 2:
        return 0.0

    first_open = float(df.iloc[0]["open"])
    last_close = float(df.iloc[-1]["close"])

    exec_entry = first_open * (1.0 + slippage_bps / 10_000.0)
    cost_factor = 1.0 + transaction_cost_bps / 10_000.0
    qty = int(initial_capital / (exec_entry * cost_factor))
    if qty == 0:
        return 0.0

    entry_fees = exec_entry * qty * transaction_cost_bps / 10_000.0
    cost_basis = exec_entry * qty + entry_fees
    remaining_cash = initial_capital - cost_basis

    exec_exit = last_close * (1.0 - slippage_bps / 10_000.0)
    exit_fees = exec_exit * qty * transaction_cost_bps / 10_000.0
    proceeds = exec_exit * qty - exit_fees

    final_equity = remaining_cash + proceeds
    return (final_equity - initial_capital) / initial_capital * 100
