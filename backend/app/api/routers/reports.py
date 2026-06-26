from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_api_key
from app.core.rate_limiter import limiter
from app.schemas.report import ReportRunResponse
from app.services.report_service import generate_report, get_latest_report

router = APIRouter(prefix="/assets", tags=["reports"])


@router.get(
    "/{symbol}/report/latest",
    response_model=ReportRunResponse,
    summary="Último relatório do ativo",
    description="Retorna o relatório analítico mais recente gerado para o ativo.",
    responses={404: {"description": "Nenhum relatório disponível para este ativo"}},
)
@limiter.limit("60/minute")
def get_latest_report_endpoint(
    request: Request,
    symbol: str,
    db: Session = Depends(get_db),
) -> object:
    run = get_latest_report(symbol.upper(), db)
    if run is None:
        raise HTTPException(status_code=404, detail="no_report_available")
    return run


@router.post(
    "/{symbol}/report/generate",
    response_model=ReportRunResponse,
    dependencies=[Depends(require_api_key)],
    summary="Gerar relatório do ativo",
    description=(
        "Gera ou retorna relatório analítico para o ativo. "
        "Idempotente: mesmo contexto no mesmo dia retorna relatório existente. "
        "Requer X-Api-Key."
    ),
    responses={
        401: {"description": "API key inválida ou ausente"},
        404: {"description": "Ativo não encontrado"},
        422: {"description": "Sinal ou snapshot indisponível"},
    },
)
@limiter.limit("10/minute")
def generate_report_endpoint(
    request: Request,
    symbol: str,
    db: Session = Depends(get_db),
) -> object:
    try:
        return generate_report(symbol.upper(), db, report_type="on_demand")
    except ValueError as exc:
        msg = str(exc)
        if msg.startswith("asset_not_found:"):
            raise HTTPException(status_code=404, detail="asset_not_found") from exc
        if msg.startswith("no_signal_available:") or msg.startswith("no_snapshot_available:"):
            detail = msg.split(":")[0]
            raise HTTPException(status_code=422, detail=detail) from exc
        raise HTTPException(status_code=422, detail=msg) from exc
