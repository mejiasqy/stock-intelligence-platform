import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.api.routers import analysis, assets, backtests, health, jobs, reports, signals
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.rate_limiter import limiter
from app.middleware.request_id import RequestIDMiddleware, request_id_var
from app.scheduler.runner import start_scheduler, stop_scheduler

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Human-readable messages for error codes
# ---------------------------------------------------------------------------

_CODE_MESSAGES: dict[str, str] = {
    "unauthorized": "Authentication required. Provide a valid X-Api-Key header.",
    "asset_not_found": "Asset not found.",
    "no_snapshot_available": "No analysis snapshot available for this asset.",
    "no_signal_available": "No signal available for this asset.",
    "backtest_run_not_found": "Backtest run not found.",
    "unknown_strategy": "Unknown backtest strategy.",
    "asset_already_exists": "An asset with this symbol already exists.",
    "no_report_available": "No report available for this asset.",
    "pipeline_already_running": "Pipeline is already running. Try again later.",
    "rate_limit_exceeded": "Too many requests. Please slow down.",
    "validation_error": "Request validation failed.",
    "internal_server_error": "An internal error occurred.",
}

_STATUS_MESSAGES: dict[int, str] = {
    400: "Bad request.",
    401: "Authentication required.",
    403: "Access denied.",
    404: "Resource not found.",
    409: "Conflict with existing resource.",
    422: "Request validation failed.",
    429: "Too many requests.",
    500: "An internal error occurred.",
}


def _resolve_message(code: str, status_code: int) -> str:
    return _CODE_MESSAGES.get(code) or _STATUS_MESSAGES.get(status_code, "An error occurred.")


def _error_body(code: str, message: str, fields: list[dict[str, str]] | None = None) -> dict:
    body: dict = {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id_var.get() or None,
        }
    }
    if fields:
        body["error"]["fields"] = fields
    return body


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    start_scheduler()
    yield
    stop_scheduler()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Stock Intelligence Platform",
    version="0.1.0",
    description=(
        "Plataforma de análise de ações, ranking, backtesting e relatórios por IA. "
        "Uso educacional e analítico — não constitui recomendação financeira."
    ),
    lifespan=lifespan,
    openapi_tags=[
        {"name": "health", "description": "Status e disponibilidade da API."},
        {"name": "assets", "description": "Cadastro de ativos e ingestão de preços históricos."},
        {"name": "analysis", "description": "Indicadores técnicos calculados por ativo."},
        {"name": "signals", "description": "Sinais analíticos e ranking de ativos por score."},
        {"name": "backtests", "description": "Execução e histórico de backtests de estratégias."},
    ],
)

app.state.limiter = limiter

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_allow_headers,
)

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    code = "rate_limit_exceeded"
    return JSONResponse(
        status_code=429,
        content=_error_body(code, _resolve_message(code, 429)),
        headers={"Retry-After": "60", "X-Request-ID": request_id_var.get() or ""},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code = exc.detail if isinstance(exc.detail, str) else "error"
    message = _resolve_message(code, exc.status_code)
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(code, message),
        headers={"X-Request-ID": request_id_var.get() or ""},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    fields = [
        {
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=_error_body("validation_error", "Request validation failed.", fields),
        headers={"X-Request-ID": request_id_var.get() or ""},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception: %s", exc, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=_error_body(
            "internal_server_error", _resolve_message("internal_server_error", 500)
        ),
        headers={"X-Request-ID": request_id_var.get() or ""},
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(health.router, prefix="/api/v1")
app.include_router(assets.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(signals.router, prefix="/api/v1")
app.include_router(backtests.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
