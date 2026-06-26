"""Testes de integração: pipeline manual, lock advisory, scheduler."""

import contextlib
from unittest.mock import patch

from sqlalchemy import text

from app.db.models.asset import Asset
from app.db.models.indicator_snapshot import IndicatorSnapshot
from app.db.models.signal import Signal
from app.db.session import engine
from app.services.pipeline_service import (
    PIPELINE_ADVISORY_LOCK_ID,
    run_daily_pipeline,
)


def _seed(db) -> None:
    asset = Asset(symbol="ITUB4.SA", name="Itaú")
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
        signal_type="bullish",
        strength=0.3,
        score=65.0,
        reason_codes={},
        pillar_scores={},
    )
    db.add(sig)
    sig.asset = asset
    db.commit()


def test_daily_pipeline_requires_api_key(client):
    resp = client.post("/api/v1/jobs/daily-pipeline/run")
    assert resp.status_code == 401


def test_daily_pipeline_manual_trigger(client, db_session):
    _seed(db_session)
    resp = client.post(
        "/api/v1/jobs/daily-pipeline/run",
        headers={"X-Api-Key": "change-me-in-production"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert "assets_processed" in data


def test_scheduler_disabled_by_default():
    from app.scheduler.runner import is_running

    assert is_running() is False


def test_pipeline_acquires_lock(db_session):
    _seed(db_session)
    result = run_daily_pipeline()
    assert result.assets_processed >= 1


def test_lock_and_unlock_same_connection():
    """Prova que duas engine.connect() geram backends PostgreSQL distintos.

    Usa pg_backend_pid() — não identidade de objeto Python — como evidência
    de conexão física independente. Verifica o ciclo completo do advisory lock:
    conn_a adquire → conn_b falha → conn_a libera → conn_b adquire.
    """
    with engine.connect() as conn_a, engine.connect() as conn_b:
        pid_a = conn_a.execute(text("SELECT pg_backend_pid()")).scalar()
        pid_b = conn_b.execute(text("SELECT pg_backend_pid()")).scalar()

        assert pid_a != pid_b, (
            f"engine.connect() deve retornar backends físicos distintos "
            f"(obtidos: pid_a={pid_a}, pid_b={pid_b})"
        )

        # conn_a adquire o advisory lock (session-level)
        acquired_a = conn_a.execute(
            text("SELECT pg_try_advisory_lock(:id)"),
            {"id": PIPELINE_ADVISORY_LOCK_ID},
        ).scalar()
        assert acquired_a is True, "conn_a deve adquirir o lock"

        # conn_b (backend diferente) NÃO consegue adquirir o mesmo lock
        acquired_b = conn_b.execute(
            text("SELECT pg_try_advisory_lock(:id)"),
            {"id": PIPELINE_ADVISORY_LOCK_ID},
        ).scalar()
        assert acquired_b is False, (
            "conn_b não deve adquirir lock mantido por conn_a (backends distintos)"
        )

        # Unlock em conn_a — mesma conexão que adquiriu
        conn_a.execute(
            text("SELECT pg_advisory_unlock(:id)"),
            {"id": PIPELINE_ADVISORY_LOCK_ID},
        )

        # Após unlock, conn_b consegue adquirir
        acquired_b_after = conn_b.execute(
            text("SELECT pg_try_advisory_lock(:id)"),
            {"id": PIPELINE_ADVISORY_LOCK_ID},
        ).scalar()
        assert acquired_b_after is True, "conn_b deve adquirir o lock após unlock de conn_a"

        # Cleanup explícito antes de devolver ao pool
        conn_b.execute(
            text("SELECT pg_advisory_unlock(:id)"),
            {"id": PIPELINE_ADVISORY_LOCK_ID},
        )


def test_pipeline_concurrent_returns_409(client):
    """Segura o advisory lock com conexão dedicada e confirma que o endpoint retorna 409."""
    with engine.connect() as ext_conn:
        acquired = ext_conn.execute(
            text("SELECT pg_try_advisory_lock(:id)"),
            {"id": PIPELINE_ADVISORY_LOCK_ID},
        ).scalar()
        assert acquired is True
        try:
            resp = client.post(
                "/api/v1/jobs/daily-pipeline/run",
                headers={"X-Api-Key": "change-me-in-production"},
            )
            assert resp.status_code == 409
            assert resp.json()["error"]["code"] == "pipeline_already_running"
        finally:
            ext_conn.execute(
                text("SELECT pg_advisory_unlock(:id)"),
                {"id": PIPELINE_ADVISORY_LOCK_ID},
            )


def test_pipeline_lock_released_after_success(db_session):
    """Após execução bem-sucedida o lock deve estar disponível para nova conexão."""
    _seed(db_session)
    run_daily_pipeline()
    with engine.connect() as verify_conn:
        acquired = verify_conn.execute(
            text("SELECT pg_try_advisory_lock(:id)"),
            {"id": PIPELINE_ADVISORY_LOCK_ID},
        ).scalar()
        assert acquired is True
        verify_conn.execute(
            text("SELECT pg_advisory_unlock(:id)"),
            {"id": PIPELINE_ADVISORY_LOCK_ID},
        )


def test_pipeline_lock_released_after_exception(db_session):
    """Após exceção não tratada em _run_pipeline_work o lock ainda é liberado (finally)."""
    _seed(db_session)
    _patch = patch(
        "app.services.pipeline_service._run_pipeline_work",
        side_effect=RuntimeError("simulated pipeline crash"),
    )
    with _patch, contextlib.suppress(RuntimeError):
        run_daily_pipeline()
    with engine.connect() as verify_conn:
        acquired = verify_conn.execute(
            text("SELECT pg_try_advisory_lock(:id)"),
            {"id": PIPELINE_ADVISORY_LOCK_ID},
        ).scalar()
        assert acquired is True
        verify_conn.execute(
            text("SELECT pg_advisory_unlock(:id)"),
            {"id": PIPELINE_ADVISORY_LOCK_ID},
        )
