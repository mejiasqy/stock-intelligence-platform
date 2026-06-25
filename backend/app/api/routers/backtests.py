from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db,
    get_pagination_params,
    get_trades_pagination_params,
    require_api_key,
)
from app.core.rate_limiter import limiter
from app.db.models.asset import Asset
from app.db.models.backtest_run import BacktestRun
from app.db.models.backtest_trade import BacktestTrade
from app.domain.backtesting.strategy import get_strategy
from app.schemas.backtest import (
    BacktestRunRead,
    BacktestRunRequest,
    BacktestRunSummary,
    BacktestTradeRead,
)
from app.schemas.pagination import PaginatedResponse, PaginationMeta
from app.services.backtest_service import execute_backtest

router = APIRouter(prefix="/backtests", tags=["backtests"])


@router.get(
    "",
    response_model=PaginatedResponse[BacktestRunSummary],
    summary="Listar backtests",
    description="Retorna histórico de runs paginado. Filtrável por símbolo e estratégia.",
    responses={422: {"description": "Parâmetros inválidos"}},
)
@limiter.limit("30/minute")
def list_backtest_runs(
    request: Request,
    symbol: str | None = Query(None, description="Filtrar por símbolo do ativo"),
    strategy_name: str | None = Query(None, description="Filtrar por nome de estratégia"),
    sort_by: Literal["created_at", "total_return_pct", "sharpe_ratio"] = Query(
        "created_at", description="Campo de ordenação"
    ),
    sort_order: Literal["asc", "desc"] = Query("desc", description="Direção da ordenação"),
    pagination: dict = Depends(get_pagination_params),
    db: Session = Depends(get_db),
) -> dict:
    limit, offset = pagination["limit"], pagination["offset"]

    query = db.query(BacktestRun)

    if symbol is not None:
        asset = db.query(Asset).filter(Asset.symbol == symbol.upper()).first()
        if asset is None:
            return {
                "items": [],
                "pagination": PaginationMeta(limit=limit, offset=offset, total=0),
            }
        query = query.filter(BacktestRun.asset_id == asset.id)

    if strategy_name is not None:
        query = query.filter(BacktestRun.strategy_name == strategy_name)

    _sort_cols = {
        "created_at": BacktestRun.created_at,
        "total_return_pct": BacktestRun.total_return_pct,
        "sharpe_ratio": BacktestRun.sharpe_ratio,
    }
    order_col = _sort_cols[sort_by]
    query = query.order_by(order_col.asc() if sort_order == "asc" else order_col.desc())

    total: int = query.count()
    items = query.offset(offset).limit(limit).all()

    return {
        "items": items,
        "pagination": PaginationMeta(limit=limit, offset=offset, total=total),
    }


@router.post(
    "/run",
    response_model=BacktestRunRead,
    dependencies=[Depends(require_api_key)],
    summary="Executar backtest",
    description="Executa e persiste um backtest com parâmetros reproduzíveis. Requer `X-Api-Key`.",
    responses={
        401: {"description": "API key inválida ou ausente"},
        404: {"description": "Ativo não encontrado"},
        422: {"description": "Estratégia desconhecida ou parâmetros inválidos"},
    },
)
@limiter.limit("10/minute")
def run_backtest_endpoint(
    request: Request,
    req: BacktestRunRequest,
    db: Session = Depends(get_db),
) -> BacktestRun:
    try:
        get_strategy(req.strategy_name)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="unknown_strategy") from exc

    try:
        return execute_backtest(db, req)
    except ValueError as exc:
        msg = str(exc)
        if msg.startswith("asset_not_found:"):
            raise HTTPException(status_code=404, detail="asset_not_found") from exc
        raise HTTPException(status_code=400, detail=msg) from exc


@router.get(
    "/{run_id}",
    response_model=BacktestRunRead,
    summary="Detalhes de um backtest",
    description="Retorna métricas, curva de equity e parâmetros de um run.",
    responses={404: {"description": "Run não encontrado"}},
)
def get_backtest_run(run_id: int, db: Session = Depends(get_db)) -> BacktestRun:
    run = db.query(BacktestRun).filter(BacktestRun.id == run_id).first()
    if run is None:
        raise HTTPException(status_code=404, detail="backtest_run_not_found")
    return run


@router.get(
    "/{run_id}/trades",
    response_model=PaginatedResponse[BacktestTradeRead],
    summary="Trades de um backtest",
    description="Retorna os trades simulados de um run, paginados.",
    responses={404: {"description": "Run não encontrado"}},
)
def get_backtest_trades(
    run_id: int,
    pagination: dict = Depends(get_trades_pagination_params),
    db: Session = Depends(get_db),
) -> dict:
    run = db.query(BacktestRun).filter(BacktestRun.id == run_id).first()
    if run is None:
        raise HTTPException(status_code=404, detail="backtest_run_not_found")
    limit, offset = pagination["limit"], pagination["offset"]
    total: int = db.query(BacktestTrade).filter(BacktestTrade.backtest_run_id == run_id).count()
    items = (
        db.query(BacktestTrade)
        .filter(BacktestTrade.backtest_run_id == run_id)
        .order_by(BacktestTrade.entry_timestamp.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "items": items,
        "pagination": PaginationMeta(limit=limit, offset=offset, total=total),
    }
