from datetime import UTC, datetime, time

import pandas as pd
from sqlalchemy.orm import Session

from app.core.constants import DEFAULT_SOURCE, DEFAULT_TIMEFRAME
from app.db.models.asset import Asset
from app.db.models.backtest_run import BacktestRun
from app.db.models.backtest_trade import BacktestTrade
from app.db.models.price_bar import PriceBar
from app.domain.backtesting.engine import BACKTEST_ENGINE_VERSION, BacktestParams, run_backtest
from app.domain.backtesting.strategy import get_strategy
from app.schemas.backtest import BacktestRunRequest


def _to_utc(d: object) -> datetime:
    from datetime import date as date_type

    if isinstance(d, date_type):
        return datetime.combine(d, time.min, tzinfo=UTC)
    return d  # type: ignore[return-value]


def execute_backtest(db: Session, req: BacktestRunRequest) -> BacktestRun:
    """Executa o backtest e persiste run + trades. Retorna o BacktestRun criado."""
    asset = db.query(Asset).filter(Asset.symbol == req.symbol.upper()).first()
    if asset is None:
        raise ValueError(f"asset_not_found:{req.symbol}")

    query = db.query(PriceBar).filter(
        PriceBar.asset_id == asset.id,
        PriceBar.timeframe == DEFAULT_TIMEFRAME,
        PriceBar.source == DEFAULT_SOURCE,
    )
    if req.start_date:
        query = query.filter(PriceBar.timestamp >= _to_utc(req.start_date))
    if req.end_date:
        query = query.filter(PriceBar.timestamp <= _to_utc(req.end_date))

    bars: list[PriceBar] = query.order_by(PriceBar.timestamp.asc()).all()

    if bars:
        df = pd.DataFrame(
            {
                "open": [float(b.open) for b in bars],
                "high": [float(b.high) for b in bars],
                "low": [float(b.low) for b in bars],
                "close": [float(b.close) for b in bars],
                "volume": [float(b.volume) for b in bars],
            },
            index=pd.DatetimeIndex([b.timestamp for b in bars]),
        )
    else:
        df = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

    strategy = get_strategy(req.strategy_name)
    params = BacktestParams(
        initial_capital=req.initial_capital,
        transaction_cost_bps=req.transaction_cost_bps,
        slippage_bps=req.slippage_bps,
        risk_free_rate_pct=req.risk_free_rate_pct,
    )

    result = run_backtest(df, strategy, params)

    parameters_snapshot: dict = {
        "strategy_name": strategy.strategy_name,
        "strategy_version": strategy.strategy_version,
        **strategy.parameters(),
        "initial_capital": req.initial_capital,
        "transaction_cost_bps": req.transaction_cost_bps,
        "slippage_bps": req.slippage_bps,
        "risk_free_rate_pct": req.risk_free_rate_pct,
        "timeframe": DEFAULT_TIMEFRAME,
        "source": DEFAULT_SOURCE,
        "engine_version": BACKTEST_ENGINE_VERSION,
    }

    def _ts(t: object) -> datetime:
        if hasattr(t, "to_pydatetime"):
            result_dt: datetime = t.to_pydatetime()
            return result_dt
        if isinstance(t, datetime):
            return t
        return datetime.fromisoformat(str(t))

    data_start = _ts(result.data_start) if result.data_start is not None else datetime.now(UTC)
    data_end = _ts(result.data_end) if result.data_end is not None else datetime.now(UTC)

    m = result.metrics

    run = BacktestRun(
        asset_id=asset.id,
        strategy_name=strategy.strategy_name,
        strategy_version=strategy.strategy_version,
        engine_version=BACKTEST_ENGINE_VERSION,
        data_start=data_start,
        data_end=data_end,
        timeframe=DEFAULT_TIMEFRAME,
        source=DEFAULT_SOURCE,
        initial_capital=req.initial_capital,
        transaction_cost_bps=req.transaction_cost_bps,
        slippage_bps=req.slippage_bps,
        risk_free_rate_pct=req.risk_free_rate_pct,
        parameters_snapshot_json=parameters_snapshot,
        status=result.status,
        final_equity=result.equity_curve[-1]["equity"] if result.equity_curve else None,
        total_return_pct=m.total_return_pct if m else None,
        annualized_return_pct=m.annualized_return_pct if m else None,
        volatility_pct=m.volatility_pct if m else None,
        sharpe_ratio=m.sharpe_ratio if m else None,
        max_drawdown_pct=m.max_drawdown_pct if m else None,
        win_rate_pct=m.win_rate_pct if m else None,
        profit_factor=m.profit_factor if m else None,
        trade_count=m.trade_count if m else None,
        exposure_pct=m.exposure_pct if m else None,
        benchmark_return_pct=result.benchmark_return_pct,
        equity_curve_json=result.equity_curve if result.equity_curve else None,
    )
    db.add(run)
    db.flush()

    for t in result.trades:
        db.add(
            BacktestTrade(
                backtest_run_id=run.id,
                entry_timestamp=_ts(t.entry_timestamp),
                exit_timestamp=_ts(t.exit_timestamp),
                entry_price=t.entry_price,
                exit_price=t.exit_price,
                executed_entry_price=t.executed_entry_price,
                executed_exit_price=t.executed_exit_price,
                quantity=t.quantity,
                gross_pnl=t.gross_pnl,
                net_pnl=t.net_pnl,
                fees_paid=t.fees_paid,
                reason_entry=t.reason_entry,
                reason_exit=t.reason_exit,
            )
        )

    db.commit()
    db.refresh(run)
    return run
