"""Serviço de alertas: avalia regras, dedup e disparo.

Semântica:
- ALERTS_ENABLED=False → atualiza alert_state (rastreamento), sem log, sem envio.
- ALERTS_ENABLED=True + ALERTS_DRY_RUN=True → log sanitizado, delivery_status="dry_run".
- ALERTS_ENABLED=True + ALERTS_DRY_RUN=False → envio real via Telegram.

Dedup: delivery_status IN ('sent','dry_run') bloqueia na janela ALERT_DEDUP_HOURS.
       delivery_status='failed' NÃO bloqueia tentativa posterior.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.alert_log import AlertLog
from app.db.models.alert_state import AlertState
from app.db.models.signal import Signal
from app.domain.alerts.dedup import is_duplicate
from app.domain.alerts.rules import (
    AlertRule,
    RuleResult,
    ScoreHighRule,
    ScoreLowRule,
    SignalChangeRule,
)
from app.domain.alerts.telegram import send_alert

logger = logging.getLogger(__name__)


@dataclass
class AlertSummary:
    rules_evaluated: int
    fired: int
    skipped_duplicate: int
    disabled: int


def evaluate_and_fire_alerts(
    signal: Signal,
    db: Session,
    report_run_id: int | None = None,
) -> AlertSummary:
    """Avalia as 3 regras de alerta para o sinal dado."""
    rules: list[AlertRule] = [
        SignalChangeRule(),
        ScoreHighRule(settings.alert_score_high_threshold),
        ScoreLowRule(settings.alert_score_low_threshold),
    ]

    fired = 0
    skipped = 0
    disabled = 0

    for rule in rules:
        state = (
            db.query(AlertState)
            .filter(
                AlertState.asset_id == signal.asset_id,
                AlertState.rule_key == rule.key,
            )
            .first()
        )

        result: RuleResult = rule.evaluate(signal, state)

        # Atualizar/criar alert_state sempre (para rastrear mudanças futuras)
        _upsert_state(db, signal.asset_id, rule.key, result.new_state_value, state)

        if not result.should_fire:
            continue

        # Alerts desabilitados: rastreia estado mas não envia nem loga
        if not settings.alerts_enabled:
            disabled += 1
            continue

        # Verificar dedup
        if is_duplicate(db, signal.asset_id, rule.key, settings.alert_dedup_hours):
            _persist_log(
                db,
                signal=signal,
                rule_key=rule.key,
                payload=result.payload,
                delivery_status="skipped_duplicate",
                is_dry_run=settings.alerts_dry_run,
                report_run_id=report_run_id,
            )
            skipped += 1
            continue

        # Enviar alerta
        delivery_status = send_alert(
            payload=result.payload,
            bot_token=settings.telegram_bot_token,
            chat_id=settings.telegram_chat_id,
            dry_run=settings.alerts_dry_run,
        )

        _persist_log(
            db,
            signal=signal,
            rule_key=rule.key,
            payload=result.payload,
            delivery_status=delivery_status,
            is_dry_run=settings.alerts_dry_run,
            report_run_id=report_run_id,
        )
        fired += 1

    db.commit()
    return AlertSummary(
        rules_evaluated=len(rules),
        fired=fired,
        skipped_duplicate=skipped,
        disabled=disabled,
    )


def _upsert_state(
    db: Session,
    asset_id: int,
    rule_key: str,
    new_value: dict,
    existing: AlertState | None,
) -> None:
    if existing is None:
        db.add(
            AlertState(
                asset_id=asset_id,
                rule_key=rule_key,
                last_observed_value_json=new_value,
                updated_at=datetime.now(UTC),
            )
        )
    else:
        existing.last_observed_value_json = new_value
        existing.updated_at = datetime.now(UTC)


def _persist_log(
    db: Session,
    *,
    signal: Signal,
    rule_key: str,
    payload: dict,
    delivery_status: str,
    is_dry_run: bool,
    report_run_id: int | None,
) -> None:
    db.add(
        AlertLog(
            asset_id=signal.asset_id,
            rule_key=rule_key,
            fired_at=datetime.now(UTC),
            payload_snapshot_json=payload,
            delivery_status=delivery_status,
            is_dry_run=is_dry_run,
            report_run_id=report_run_id,
            signal_id=signal.id,
        )
    )
