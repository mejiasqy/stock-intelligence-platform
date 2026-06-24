from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.core.config import settings
from app.db.models.backtest_run import BacktestRun
from app.db.models.backtest_trade import BacktestTrade
from app.domain.backtesting.strategy import get_strategy
from app.schemas.backtest import BacktestRunRead, BacktestRunRequest, BacktestTradeRead
from app.services.backtest_service import execute_backtest

router = APIRouter(prefix="/backtests", tags=["backtests"])


def _require_api_key(x_api_key: str = Header(..., alias="X-Api-Key")) -> None:
    if x_api_key != settings.api_secret_key:
        raise HTTPException(status_code=401, detail="invalid_api_key")


@router.post("/run", response_model=BacktestRunRead, dependencies=[Depends(_require_api_key)])
def run_backtest_endpoint(req: BacktestRunRequest, db: Session = Depends(get_db)) -> BacktestRun:
    """Executa um backtest e persiste os resultados.

    Requer `X-Api-Key`. Parâmetros e versão do motor ficam registrados para
    reprodutibilidade. Retorna 404 se o ativo não existir.
    """
    try:
        get_strategy(req.strategy_name)
    except ValueError as exc:
        raise HTTPException(
            status_code=422, detail=f"unknown_strategy:{req.strategy_name}"
        ) from exc

    try:
        return execute_backtest(db, req)
    except ValueError as exc:
        msg = str(exc)
        if msg.startswith("asset_not_found:"):
            raise HTTPException(status_code=404, detail="asset_not_found") from exc
        raise HTTPException(status_code=400, detail=msg) from exc


@router.get("/{run_id}", response_model=BacktestRunRead)
def get_backtest_run(run_id: int, db: Session = Depends(get_db)) -> BacktestRun:
    """Retorna métricas, curva de equity e parâmetros de um run."""
    run = db.query(BacktestRun).filter(BacktestRun.id == run_id).first()
    if run is None:
        raise HTTPException(status_code=404, detail="backtest_run_not_found")
    return run


@router.get("/{run_id}/trades", response_model=list[BacktestTradeRead])
def get_backtest_trades(
    run_id: int,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> list[BacktestTrade]:
    """Retorna os trades simulados de um run, paginados."""
    run = db.query(BacktestRun).filter(BacktestRun.id == run_id).first()
    if run is None:
        raise HTTPException(status_code=404, detail="backtest_run_not_found")
    return (
        db.query(BacktestTrade)
        .filter(BacktestTrade.backtest_run_id == run_id)
        .order_by(BacktestTrade.entry_timestamp.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
