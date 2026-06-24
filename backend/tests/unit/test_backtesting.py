"""Testes unitários do motor de backtesting — funções puras sem banco."""


import pandas as pd
import pytest

from app.domain.backtesting.engine import BacktestParams, run_backtest
from app.domain.backtesting.metrics import compute_benchmark, compute_metrics
from app.domain.backtesting.strategy import SMACrossover

# ---------------------------------------------------------------------------
# Fixtures helpers
# ---------------------------------------------------------------------------


def _make_df(prices: list[float], opens: list[float] | None = None) -> pd.DataFrame:
    """Cria DataFrame com preços OHLCV para testes; open = close por padrão."""
    n = len(prices)
    o = opens if opens is not None else prices
    dates = pd.date_range("2023-01-02", periods=n, freq="B", tz="UTC")
    return pd.DataFrame(
        {
            "open": o,
            "high": [p * 1.01 for p in prices],
            "low": [p * 0.99 for p in prices],
            "close": prices,
            "volume": [1_000_000] * n,
        },
        index=dates,
    )


def _default_params(**kwargs: object) -> BacktestParams:
    base = dict(
        initial_capital=100_000.0, transaction_cost_bps=0, slippage_bps=0, risk_free_rate_pct=0.0
    )
    base.update(kwargs)
    return BacktestParams(**base)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# SMACrossover — interface
# ---------------------------------------------------------------------------


def test_sma_crossover_min_bars() -> None:
    assert SMACrossover(fast_period=3, slow_period=5).min_bars_required() == 6


def test_sma_crossover_parameters() -> None:
    s = SMACrossover(fast_period=3, slow_period=5)
    assert s.parameters() == {"fast_period": 3, "slow_period": 5}


def test_sma_crossover_rejects_fast_ge_slow() -> None:
    with pytest.raises(ValueError):
        SMACrossover(fast_period=10, slow_period=5)


# ---------------------------------------------------------------------------
# SMACrossover — geração de sinais
# ---------------------------------------------------------------------------


def test_sma_crossover_buy_signal_on_known_series() -> None:
    # preços sobem após bar 4: SMA3 cruza acima SMA5 em algum ponto
    prices = [10.0] * 5 + [20.0] * 10
    df = _make_df(prices)
    s = SMACrossover(fast_period=3, slow_period=5)
    signals = s.generate_signals(df)
    assert "buy" in signals.values


def test_sma_crossover_sell_signal_on_known_series() -> None:
    # sobe depois cai: deve haver buy E sell
    prices = [10.0] * 5 + [20.0] * 8 + [10.0] * 8
    df = _make_df(prices)
    s = SMACrossover(fast_period=3, slow_period=5)
    signals = s.generate_signals(df)
    assert "buy" in signals.values
    assert "sell" in signals.values


def test_sma_crossover_no_signal_on_flat_series() -> None:
    prices = [10.0] * 20
    df = _make_df(prices)
    s = SMACrossover(fast_period=3, slow_period=5)
    signals = s.generate_signals(df)
    assert "buy" not in signals.values
    assert "sell" not in signals.values


# ---------------------------------------------------------------------------
# Engine — estados básicos
# ---------------------------------------------------------------------------


def test_engine_insufficient_data() -> None:
    prices = [10.0] * 5  # < min_bars_required(6)
    df = _make_df(prices)
    result = run_backtest(df, SMACrossover(fast_period=3, slow_period=5), _default_params())
    assert result.status == "insufficient_data"
    assert result.trades == []
    assert result.metrics is None


def test_engine_zero_trades_flat_series() -> None:
    # Série plana — sem cruzamento → sem trades
    prices = [10.0] * 30
    df = _make_df(prices)
    result = run_backtest(df, SMACrossover(fast_period=3, slow_period=5), _default_params())
    assert result.status == "completed"
    assert len(result.trades) == 0
    assert result.metrics is not None
    assert result.metrics.trade_count == 0
    assert result.metrics.win_rate_pct is None
    assert result.metrics.profit_factor is None


def test_engine_equity_curve_length_matches_bars() -> None:
    prices = [10.0] * 30
    df = _make_df(prices)
    result = run_backtest(df, SMACrossover(fast_period=3, slow_period=5), _default_params())
    assert len(result.equity_curve) == len(df)


# ---------------------------------------------------------------------------
# Engine — custos e slippage
# ---------------------------------------------------------------------------


def test_engine_costs_reduce_net_pnl() -> None:
    prices = [10.0] * 5 + [20.0] * 10 + [10.0] * 8
    df = _make_df(prices)
    strategy = SMACrossover(fast_period=3, slow_period=5)

    r_no_cost = run_backtest(df, strategy, _default_params(transaction_cost_bps=0, slippage_bps=0))
    r_with_cost = run_backtest(
        df, strategy, _default_params(transaction_cost_bps=20, slippage_bps=0)
    )

    if r_no_cost.trades and r_with_cost.trades:
        assert r_with_cost.trades[0].net_pnl < r_no_cost.trades[0].net_pnl
        assert r_with_cost.trades[0].fees_paid > 0


def test_engine_slippage_adjusts_execution_price() -> None:
    prices = [10.0] * 5 + [20.0] * 10
    df = _make_df(prices, opens=[p for p in ([10.0] * 5 + [20.0] * 10)])
    strategy = SMACrossover(fast_period=3, slow_period=5)
    r = run_backtest(df, strategy, _default_params(slippage_bps=100))  # 1% slippage

    if r.trades:
        t = r.trades[0]
        expected_exec = t.entry_price * (1 + 100 / 10_000)
        assert abs(t.executed_entry_price - expected_exec) < 0.001


# ---------------------------------------------------------------------------
# Engine — look-ahead bias
# ---------------------------------------------------------------------------


def test_engine_no_look_ahead_bias() -> None:
    """Modificar barras futuras não deve alterar trades já concluídos antes delas."""
    prices_base = [10.0] * 5 + [20.0] * 10 + [10.0] * 8 + [20.0] * 5
    df1 = _make_df(prices_base)
    strategy = SMACrossover(fast_period=3, slow_period=5)
    result1 = run_backtest(df1, strategy, _default_params())

    # Duplica preços na segunda metade — completamente diferente
    prices_modified = prices_base[:14] + [p * 2 for p in prices_base[14:]]
    df2 = _make_df(prices_modified)
    result2 = run_backtest(df2, strategy, _default_params())

    # Trades que terminaram antes do bar 14 devem ser idênticos
    cutoff = df1.index[13]
    early_trades_1 = [t for t in result1.trades if t.exit_timestamp <= cutoff]
    early_trades_2 = [t for t in result2.trades if t.exit_timestamp <= cutoff]

    assert len(early_trades_1) == len(early_trades_2)
    for t1, t2 in zip(early_trades_1, early_trades_2, strict=False):
        assert t1.entry_timestamp == t2.entry_timestamp
        assert t1.exit_timestamp == t2.exit_timestamp
        assert abs(t1.net_pnl - t2.net_pnl) < 0.001


# ---------------------------------------------------------------------------
# Engine — fechamento forçado no fim do período
# ---------------------------------------------------------------------------


def test_engine_end_of_period_force_close() -> None:
    # Série que compra mas nunca gera sell antes do fim
    prices = [10.0] * 5 + [20.0] * 15
    df = _make_df(prices)
    strategy = SMACrossover(fast_period=3, slow_period=5)
    result = run_backtest(df, strategy, _default_params())
    # Se entrou, deve ter saído com reason_exit="end_of_period"
    if result.trades:
        assert any(t.reason_exit == "end_of_period" for t in result.trades)


# ---------------------------------------------------------------------------
# Métricas
# ---------------------------------------------------------------------------


def test_metrics_total_return_positive() -> None:
    curve = [
        {"date": "2024-01-01", "equity": 100_000.0},
        {"date": "2024-01-02", "equity": 110_000.0},
    ]
    m = compute_metrics(curve, [10_000.0], 1, 100_000.0, 0.0)
    assert abs(m.total_return_pct - 10.0) < 0.001


def test_metrics_max_drawdown_zero_on_monotone_up() -> None:
    curve = [
        {"date": f"2024-01-{i:02d}", "equity": float(100_000 + i * 1000)} for i in range(1, 11)
    ]
    m = compute_metrics(curve, [], 0, 100_000.0, 0.0)
    assert m.max_drawdown_pct == pytest.approx(0.0, abs=0.01)


def test_metrics_win_rate_all_winners() -> None:
    curve = [
        {"date": "2024-01-01", "equity": 100_000.0},
        {"date": "2024-01-10", "equity": 105_000.0},
    ]
    m = compute_metrics(curve, [1000.0, 2000.0], 5, 100_000.0, 0.0)
    assert m.win_rate_pct == pytest.approx(100.0)


def test_metrics_profit_factor_none_when_no_losses() -> None:
    curve = [
        {"date": "2024-01-01", "equity": 100_000.0},
        {"date": "2024-01-10", "equity": 105_000.0},
    ]
    m = compute_metrics(curve, [500.0, 1000.0], 5, 100_000.0, 0.0)
    assert m.profit_factor is None


def test_metrics_sharpe_none_when_zero_volatility() -> None:
    # Equity constante → std = 0 → sharpe = None
    curve = [{"date": f"2024-01-{i:02d}", "equity": 100_000.0} for i in range(1, 11)]
    m = compute_metrics(curve, [], 0, 100_000.0, 0.0)
    assert m.sharpe_ratio is None


# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------


def test_benchmark_buy_and_hold_no_cost() -> None:
    prices = [10.0] * 5 + [20.0] * 5
    df = _make_df(prices)
    # Com open=close=10 no início e close=20 no fim, retorno ~100%
    bm = compute_benchmark(df, 100_000.0, 0, 0)
    assert bm > 90.0  # deve ser próximo de 100%


def test_benchmark_costs_reduce_return() -> None:
    prices = [10.0] * 5 + [20.0] * 5
    df = _make_df(prices)
    bm_no_cost = compute_benchmark(df, 100_000.0, 0, 0)
    bm_with_cost = compute_benchmark(df, 100_000.0, 50, 50)
    assert bm_with_cost < bm_no_cost


def test_benchmark_insufficient_data_returns_zero() -> None:
    df = _make_df([10.0])
    assert compute_benchmark(df, 100_000.0, 10, 10) == 0.0
