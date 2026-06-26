from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.dependencies import require_api_key
from app.core.rate_limiter import limiter
from app.services.pipeline_service import PipelineAlreadyRunningError, run_daily_pipeline

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post(
    "/daily-pipeline/run",
    dependencies=[Depends(require_api_key)],
    summary="Disparar pipeline diário manualmente",
    description=(
        "Executa o pipeline completo (geração de relatórios + alertas) para todos os ativos "
        "com sinal. Idempotente por ativo/dia/contexto. Requer X-Api-Key."
    ),
    responses={
        401: {"description": "API key inválida ou ausente"},
        409: {"description": "Pipeline já em execução"},
    },
)
@limiter.limit("5/minute")
def run_pipeline(request: Request) -> dict:
    try:
        result = run_daily_pipeline()
    except PipelineAlreadyRunningError:
        raise HTTPException(status_code=409, detail="pipeline_already_running") from None

    return {
        "status": "completed",
        "assets_processed": result.assets_processed,
        "reports_generated": result.reports_generated,
        "reports_skipped_idempotent": result.reports_skipped_idempotent,
        "alerts_fired": result.alerts_fired,
    }
