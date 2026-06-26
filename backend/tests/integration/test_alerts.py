"""Testes de integração: alertas, dry-run, dedup e alert_state."""

from unittest.mock import patch

from app.db.models.alert_log import AlertLog
from app.db.models.alert_state import AlertState
from app.db.models.asset import Asset
from app.db.models.indicator_snapshot import IndicatorSnapshot
from app.db.models.signal import Signal
from app.services.alert_service import evaluate_and_fire_alerts


def _seed(db, signal_type="bullish", score=75.0):
    asset = Asset(symbol="VALE3.SA", name="Vale")
    db.add(asset)
    db.flush()
    snap = IndicatorSnapshot(
        asset_id=asset.id,
        timeframe="1d",
        source="yfinance",
        calculation_version="1.0.0",
        candles_used=250,
        status="ok",
    )
    db.add(snap)
    db.flush()
    sig = Signal(
        asset_id=asset.id,
        snapshot_id=snap.id,
        strategy_version="1.0.0",
        signal_type=signal_type,
        strength=0.3,
        score=score,
        reason_codes={},
        pillar_scores={},
    )
    db.add(sig)
    sig.asset = asset
    db.commit()
    return asset, sig


def _patch_alerts(enabled=True, dry_run=True, high=70.0, low=25.0, dedup=24):
    return patch(
        "app.services.alert_service.settings",
        **{
            "alerts_enabled": enabled,
            "alerts_dry_run": dry_run,
            "alert_score_high_threshold": high,
            "alert_score_low_threshold": low,
            "alert_dedup_hours": dedup,
            "telegram_bot_token": "test-token",
            "telegram_chat_id": "test-chat",
        },
    )


def test_telegram_dry_run_no_network(db_session):
    _, sig = _seed(db_session, score=75.0)
    _httpx = "app.domain.alerts.telegram.httpx"
    with _patch_alerts(enabled=True, dry_run=True), patch(_httpx) as mock_httpx:
        evaluate_and_fire_alerts(sig, db_session)
        mock_httpx.post.assert_not_called()


def test_sent_alert_enters_dedup(db_session):
    _, sig = _seed(db_session, score=80.0)
    # Primeira observação: grava state, não dispara
    with _patch_alerts(enabled=True, dry_run=True):
        evaluate_and_fire_alerts(sig, db_session)
    # Segunda observação: dispara score_high
    with _patch_alerts(enabled=True, dry_run=True):
        evaluate_and_fire_alerts(sig, db_session)
    # Terceira: dedup deve bloquear
    with _patch_alerts(enabled=True, dry_run=True):
        evaluate_and_fire_alerts(sig, db_session)
    skipped_logs = (
        db_session.query(AlertLog).filter(AlertLog.delivery_status == "skipped_duplicate").count()
    )
    assert skipped_logs >= 1


def test_failed_alert_not_blocking_integration(db_session):
    _, sig = _seed(db_session, score=80.0)
    _httpx = "app.domain.alerts.telegram.httpx"
    # Primeira: grava state
    with _patch_alerts(enabled=True, dry_run=False), patch(_httpx) as mock_h:
        mock_h.post.side_effect = RuntimeError("network error")
        evaluate_and_fire_alerts(sig, db_session)
    # Second observation: score_high fires but send fails → delivery_status=failed
    with _patch_alerts(enabled=True, dry_run=False), patch(_httpx) as mock_h:
        mock_h.post.side_effect = RuntimeError("network error")
        evaluate_and_fire_alerts(sig, db_session)
    # Failed should not block next attempt
    failed = db_session.query(AlertLog).filter(AlertLog.delivery_status == "failed").count()
    assert failed >= 1


def test_dry_run_no_http_call(db_session):
    _, sig = _seed(db_session, signal_type="bullish")
    _httpx = "app.domain.alerts.telegram.httpx"
    with _patch_alerts(enabled=True, dry_run=True), patch(_httpx) as mock_h:
        evaluate_and_fire_alerts(sig, db_session)
        mock_h.post.assert_not_called()


def test_signal_change_uses_alert_state(db_session):
    asset, sig = _seed(db_session, signal_type="bullish", score=55.0)
    # Primeira obs: grava state bullish, não dispara
    with _patch_alerts(enabled=True, dry_run=True):
        evaluate_and_fire_alerts(sig, db_session)
    state = (
        db_session.query(AlertState)
        .filter(AlertState.asset_id == asset.id, AlertState.rule_key == "signal_change")
        .first()
    )
    assert state is not None
    assert state.last_observed_value_json["signal_type"] == "bullish"
    # Mudar sinal para bearish
    sig.signal_type = "bearish"
    db_session.flush()
    with _patch_alerts(enabled=True, dry_run=True):
        evaluate_and_fire_alerts(sig, db_session)
    logs = (
        db_session.query(AlertLog)
        .filter(
            AlertLog.rule_key == "signal_change",
            AlertLog.delivery_status == "dry_run",
        )
        .count()
    )
    assert logs >= 1


def test_score_high_rule_fires(db_session):
    _, sig = _seed(db_session, score=80.0)
    with _patch_alerts(enabled=True, dry_run=True, high=70.0):
        evaluate_and_fire_alerts(sig, db_session)  # first: no fire
    with _patch_alerts(enabled=True, dry_run=True, high=70.0):
        evaluate_and_fire_alerts(sig, db_session)  # second: fires
    logs = db_session.query(AlertLog).filter(AlertLog.rule_key == "score_high").count()
    assert logs >= 1


def test_score_low_rule_fires(db_session):
    _, sig = _seed(db_session, score=20.0)
    with _patch_alerts(enabled=True, dry_run=True, low=25.0):
        evaluate_and_fire_alerts(sig, db_session)  # first: no fire
    with _patch_alerts(enabled=True, dry_run=True, low=25.0):
        evaluate_and_fire_alerts(sig, db_session)  # second: fires
    logs = db_session.query(AlertLog).filter(AlertLog.rule_key == "score_low").count()
    assert logs >= 1
