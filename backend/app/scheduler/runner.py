"""Scheduler do pipeline diário.

Usa BackgroundScheduler (APScheduler síncrono) em thread separada —
consistente com a stack síncrona do projeto (sem asyncio).
Inicia SOMENTE se SCHEDULER_ENABLED=true.

Nota: o horário DAILY_JOB_TIME não representa calendário de pregão; é apenas
o momento de disparo configurável para fins de demonstração educacional.
"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.services.pipeline_service import PipelineAlreadyRunningError, run_daily_pipeline

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _scheduled_job() -> None:
    logger.info("Scheduler: iniciando pipeline diário")
    try:
        result = run_daily_pipeline()
        logger.info(
            "Scheduler: pipeline concluído — ativos=%d relatórios=%d alertas=%d",
            result.assets_processed,
            result.reports_generated,
            result.alerts_fired,
        )
    except PipelineAlreadyRunningError:
        logger.warning("Scheduler: pipeline já em execução, ignorando disparo.")
    except Exception as exc:
        logger.error("Scheduler: pipeline falhou: %s", type(exc).__name__)


def start_scheduler() -> None:
    """Inicia o BackgroundScheduler se SCHEDULER_ENABLED=true."""
    global _scheduler  # noqa: PLW0603

    if not settings.scheduler_enabled:
        logger.info("Scheduler desabilitado (SCHEDULER_ENABLED=false).")
        return

    hour_str, minute_str = settings.daily_job_time.split(":")
    trigger = CronTrigger(
        hour=int(hour_str),
        minute=int(minute_str),
        timezone=settings.daily_job_timezone,
    )

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(_scheduled_job, trigger=trigger, id="daily_pipeline", replace_existing=True)
    _scheduler.start()
    logger.info(
        "Scheduler iniciado: job diário às %s (%s)",
        settings.daily_job_time,
        settings.daily_job_timezone,
    )


def stop_scheduler() -> None:
    """Para o scheduler se estiver rodando."""
    global _scheduler  # noqa: PLW0603
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler encerrado.")


def is_running() -> bool:
    return _scheduler is not None and _scheduler.running
