"""Deduplicação de alertas via janela de tempo em alert_log.

Alertas com delivery_status 'sent' ou 'dry_run' bloqueiam reenvio na janela.
Alertas com delivery_status 'failed' NÃO bloqueiam — permitem nova tentativa.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.db.models.alert_log import AlertLog

_BLOCKING_STATUSES = ("sent", "dry_run")


def is_duplicate(db: Session, asset_id: int, rule_key: str, dedup_hours: int) -> bool:
    """Retorna True se já existe alerta bloqueante para asset_id+rule_key na janela."""
    cutoff = datetime.now(UTC) - timedelta(hours=dedup_hours)
    exists = (
        db.query(AlertLog)
        .filter(
            AlertLog.asset_id == asset_id,
            AlertLog.rule_key == rule_key,
            AlertLog.fired_at >= cutoff,
            AlertLog.delivery_status.in_(_BLOCKING_STATUSES),
        )
        .first()
    )
    return exists is not None
