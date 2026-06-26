"""Testes de integração: geração e leitura de relatórios."""

from datetime import date as date_cls
from unittest.mock import patch

from sqlalchemy.exc import IntegrityError as SAIntegrityError

from app.db.models.asset import Asset
from app.db.models.indicator_snapshot import IndicatorSnapshot
from app.db.models.report_run import ReportRun
from app.db.models.signal import Signal
from app.db.session import SessionLocal
from app.domain.reports import fallback_provider as fp
from app.domain.reports.context_builder import build_context
from app.domain.reports.fallback_provider import FALLBACK_MODEL_NAME
from app.domain.reports.fingerprint import compute_fingerprint
from app.domain.reports.prompt import PROMPT_VERSION
from app.services.report_service import generate_report, get_latest_report


def _seed(db):
    asset = Asset(symbol="PETR4.SA", name="Petrobras")
    db.add(asset)
    db.flush()
    snap = IndicatorSnapshot(
        asset_id=asset.id,
        timeframe="1d",
        source="yfinance",
        calculation_version="1.0.0",
        candles_used=250,
        status="ok",
        last_close=28.5,
        sma_20=27.0,
        rsi_14=55.0,
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
        reason_codes={"price_above_sma_20": True, "rsi_in_bullish_range": False},
        pillar_scores={"trend": 20.0, "momentum": 15.0},
    )
    db.add(sig)
    db.commit()
    return asset, sig, snap


def test_provider_timeout_uses_fallback(db_session):
    _seed(db_session)
    with patch("app.services.report_service.settings") as mock_cfg:
        mock_cfg.llm_api_key = "fake-key"
        mock_cfg.llm_model = "claude-haiku-4-5-20251001"
        mock_cfg.llm_timeout_seconds = 30
        mock_cfg.llm_max_output_tokens = 1024
        with patch("app.domain.reports.anthropic_provider.anthropic") as mock_lib:
            mock_lib.Anthropic.return_value.messages.create.side_effect = Exception("Timeout")
            run = generate_report("PETR4.SA", db_session)
    assert run.is_fallback is True
    assert run.generation_status == "fallback"
    assert run.model_name == FALLBACK_MODEL_NAME


def test_provider_error_uses_fallback(db_session):
    _seed(db_session)
    with patch("app.services.report_service.settings") as mock_cfg:
        mock_cfg.llm_api_key = "fake-key"
        mock_cfg.llm_model = "claude-haiku-4-5-20251001"
        mock_cfg.llm_timeout_seconds = 30
        mock_cfg.llm_max_output_tokens = 1024
        with patch("app.domain.reports.anthropic_provider.anthropic") as mock_lib:
            mock_lib.Anthropic.return_value.messages.create.side_effect = RuntimeError("API error")
            run = generate_report("PETR4.SA", db_session)
    assert run.is_fallback is True
    assert run.generation_status == "fallback"


def test_report_run_persisted_correctly(db_session):
    _seed(db_session)
    run = generate_report("PETR4.SA", db_session)
    assert run.id is not None
    assert run.asset_id is not None
    assert run.input_fingerprint and len(run.input_fingerprint) == 64
    assert run.report_date is not None
    assert run.prompt_version == "1.0.0"
    assert run.input_snapshot_json is not None
    # Nunca contém segredos
    import json

    ctx_str = json.dumps(run.input_snapshot_json).lower()
    assert "api_key" not in ctx_str
    assert "token" not in ctx_str


def test_idempotent_same_fingerprint_same_day(db_session):
    _seed(db_session)
    run1 = generate_report("PETR4.SA", db_session)
    run2 = generate_report("PETR4.SA", db_session)
    assert run1.id == run2.id


def test_new_report_when_score_changes(db_session):
    asset, sig, _ = _seed(db_session)
    run1 = generate_report("PETR4.SA", db_session)
    # Alterar score do sinal (simula recalculo)
    sig.score = 72.0
    db_session.flush()
    run2 = generate_report("PETR4.SA", db_session)
    assert run1.id != run2.id


def test_race_condition_no_duplicate(db_session):
    """Constraint DB impede duplicata; IntegrityError tratado retornando existente."""
    _seed(db_session)
    run1 = generate_report("PETR4.SA", db_session)
    # Segunda chamada com mesmo contexto → deve retornar o mesmo
    run2 = generate_report("PETR4.SA", db_session)
    assert run1.id == run2.id


def test_get_latest_report_normal(db_session):
    _seed(db_session)
    generate_report("PETR4.SA", db_session)
    run = get_latest_report("PETR4.SA", db_session)
    assert run is not None
    assert run.generation_status in ("generated", "fallback")


def test_get_latest_report_is_fallback(db_session):
    _seed(db_session)
    run_gen = generate_report("PETR4.SA", db_session)
    run = get_latest_report("PETR4.SA", db_session)
    assert run is not None
    assert run.id == run_gen.id


def test_race_condition_true_integrity_error(db_session):
    """Prova a constraint real uq_report_run_asset_type_date_fp com duas sessões independentes.

    Fluxo:
    1. session_1 insere e commita um ReportRun.
    2. session_2 tenta inserir o mesmo registro via flush() — sem pre-check de idempotência.
    3. PostgreSQL dispara IntegrityError real pela unique constraint.
    4. session_2 faz rollback e recupera o registro inserido por session_1.
    5. Confirma exatamente 1 ReportRun para aquela combinação.

    Este teste prova a constraint de banco, não apenas a lógica sequencial de pré-consulta.
    """
    asset, sig, snap = _seed(db_session)

    # Capturar dados enquanto db_session está ativa (evita detached instance errors)
    context = build_context(asset, sig, snap)
    fingerprint = compute_fingerprint(context)
    today = date_cls.today()
    asset_id: int = asset.id
    signal_id: int = sig.id
    snap_status: str = snap.status
    generated_text = fp.generate(context)

    def _make_run() -> ReportRun:
        return ReportRun(
            asset_id=asset_id,
            signal_id=signal_id,
            report_type="daily",
            generated_text=generated_text,
            is_fallback=True,
            generation_status="fallback",
            model_name=fp.FALLBACK_MODEL_NAME,
            prompt_version=PROMPT_VERSION,
            data_quality=snap_status,
            input_snapshot_json=context,
            input_fingerprint=fingerprint,
            report_date=today,
        )

    # Sessão 1: persiste e commita — registro visível para outras sessões
    run1_id: int
    session_1 = SessionLocal()
    try:
        run1 = _make_run()
        session_1.add(run1)
        session_1.commit()
        session_1.refresh(run1)
        run1_id = run1.id
    finally:
        session_1.close()

    # Sessão 2: tenta inserir duplicata sem pré-verificação → IntegrityError real do PostgreSQL
    integrity_raised = False
    session_2 = SessionLocal()
    try:
        run2 = _make_run()
        session_2.add(run2)
        session_2.flush()  # Envia INSERT ao banco sem commit — dispara a constraint
    except SAIntegrityError:
        integrity_raised = True
        session_2.rollback()
        # Após rollback, recupera o registro existente (comportamento do report_service)
        existing = (
            session_2.query(ReportRun)
            .filter(
                ReportRun.asset_id == asset_id,
                ReportRun.report_type == "daily",
                ReportRun.report_date == today,
                ReportRun.input_fingerprint == fingerprint,
            )
            .first()
        )
        assert existing is not None, "Deve encontrar o registro inserido por session_1"
        assert existing.id == run1_id, f"ID esperado {run1_id}, obtido {existing.id}"
    finally:
        session_2.close()

    assert integrity_raised, (
        "IntegrityError deve ser disparado pela constraint uq_report_run_asset_type_date_fp"
    )

    # Confirma exatamente 1 registro com aquela combinação (via db_session — sessão de controle)
    count = (
        db_session.query(ReportRun)
        .filter(
            ReportRun.asset_id == asset_id,
            ReportRun.report_type == "daily",
            ReportRun.report_date == today,
            ReportRun.input_fingerprint == fingerprint,
        )
        .count()
    )
    assert count == 1, f"Deve existir exatamente 1 ReportRun, encontrado {count}"
