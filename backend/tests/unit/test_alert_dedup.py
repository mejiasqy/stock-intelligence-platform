"""Testes de deduplicação de alertas."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from app.domain.alerts.dedup import is_duplicate


def _make_log(status, hours_ago=1):
    log = MagicMock()
    log.delivery_status = status
    log.fired_at = datetime.now(UTC) - timedelta(hours=hours_ago)
    return log


def _db_with(log_or_none):
    db = MagicMock()
    q = MagicMock()
    db.query.return_value = q
    q.filter.return_value = q
    q.first.return_value = log_or_none
    return db


def test_sent_alert_within_window_is_duplicate():
    db = _db_with(_make_log("sent", hours_ago=2))
    assert is_duplicate(db, 1, "signal_change", 24) is True


def test_sent_alert_outside_window_not_duplicate():
    db = _db_with(None)
    assert is_duplicate(db, 1, "signal_change", 24) is False


def test_failed_alert_not_blocking():
    # failed não aparece na query (filtro IN ('sent','dry_run')), db retorna None
    db = _db_with(None)
    assert is_duplicate(db, 1, "signal_change", 24) is False


def test_dry_run_counts_as_duplicate():
    db = _db_with(_make_log("dry_run", hours_ago=1))
    assert is_duplicate(db, 1, "score_high", 24) is True
