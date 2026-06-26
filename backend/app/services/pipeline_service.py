"""Pipeline diário: geração de relatórios + avaliação de alertas para todos os ativos.

Advisory lock via PostgreSQL pg_try_advisory_lock (session-level):
- O lock é adquirido sobre uma Connection dedicada, obtida diretamente do engine.
- Toda a sessão do pipeline é criada com sessionmaker(bind=lock_conn), vinculando-a
  explicitamente a essa conexão física.
- Commits internos dos serviços (generate_report, evaluate_and_fire_alerts) não devolvem
  lock_conn ao pool porque a conexão é de propriedade do context manager 'with engine.connect()'.
- O unlock ocorre em finally sobre a mesma lock_conn, garantido mesmo em exceção.
- Múltiplos processos conectados ao mesmo PostgreSQL são protegidos.
- Nota: não há lock distribuído entre bancos distintos (fora do escopo).
"""

import logging
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import engine
from app.services.alert_service import evaluate_and_fire_alerts
from app.services.report_service import generate_report

logger = logging.getLogger(__name__)

PIPELINE_ADVISORY_LOCK_ID = 7481234567


class PipelineAlreadyRunningError(Exception):
    pass


@dataclass
class PipelineResult:
    assets_processed: int
    reports_generated: int
    reports_skipped_idempotent: int
    alerts_fired: int


def run_daily_pipeline() -> PipelineResult:
    """Executa o pipeline completo usando uma conexão dedicada para o advisory lock.

    Fluxo de segurança do lock:
    1. Abre Connection dedicada (lock_conn) — nunca devolvida ao pool durante a execução.
    2. Adquire pg_try_advisory_lock em lock_conn.
    3. Cria sessão vinculada a lock_conn via sessionmaker(bind=lock_conn).
    4. Executa todo o pipeline usando apenas essa sessão vinculada.
    5. finally: pg_advisory_unlock na mesma lock_conn, inclusive em exceção.
    6. Sessão e conexão fechadas após unlock.
    """
    with engine.connect() as lock_conn:
        acquired = lock_conn.execute(
            text("SELECT pg_try_advisory_lock(:lock_id)"),
            {"lock_id": PIPELINE_ADVISORY_LOCK_ID},
        ).scalar()

        if not acquired:
            raise PipelineAlreadyRunningError("Pipeline já em execução neste servidor PostgreSQL.")

        # Sessão vinculada à conexão dedicada.
        # sessionmaker(bind=lock_conn) — mesmo padrão de session.py com bind=engine.
        # Commits internos encerram transações mas NÃO liberam lock_conn ao pool,
        # pois a conexão é externa à sessão (gerenciada pelo context manager acima).
        bound_session_factory = sessionmaker(bind=lock_conn, autocommit=False, autoflush=False)
        pipeline_session: Session = bound_session_factory()

        try:
            result = _run_pipeline_work(pipeline_session)
        finally:
            pipeline_session.close()
            # Unlock garantido na mesma lock_conn que adquiriu o lock.
            lock_conn.execute(
                text("SELECT pg_advisory_unlock(:lock_id)"),
                {"lock_id": PIPELINE_ADVISORY_LOCK_ID},
            )

    return result


def _run_pipeline_work(db: Session) -> PipelineResult:
    from app.db.models.signal import Signal

    assets_processed = 0
    reports_generated = 0
    reports_skipped = 0
    alerts_fired = 0

    signals = db.query(Signal).all()

    for signal in signals:
        assets_processed += 1
        symbol: str = signal.asset.symbol if signal.asset else ""
        if not symbol:
            continue

        try:
            run = generate_report(symbol, db, report_type="daily")
            if run.id and run.generation_status in ("generated", "fallback"):
                reports_generated += 1
            else:
                reports_skipped += 1
        except ValueError as exc:
            logger.warning("Relatório ignorado para %s: %s", symbol, exc)
            reports_skipped += 1
            continue
        except Exception as exc:
            logger.error("Erro ao gerar relatório para %s: %s", symbol, type(exc).__name__)
            reports_skipped += 1
            continue

        try:
            summary = evaluate_and_fire_alerts(signal, db, report_run_id=run.id)
            alerts_fired += summary.fired
        except Exception as exc:
            logger.error("Erro ao avaliar alertas para %s: %s", symbol, type(exc).__name__)

    return PipelineResult(
        assets_processed=assets_processed,
        reports_generated=reports_generated,
        reports_skipped_idempotent=reports_skipped,
        alerts_fired=alerts_fired,
    )
