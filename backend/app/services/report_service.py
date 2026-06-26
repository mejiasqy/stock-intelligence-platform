"""Serviço de geração e leitura de relatórios analíticos.

Fluxo de generate_report:
1. Busca Signal + IndicatorSnapshot
2. Constrói contexto (sem segredos)
3. Calcula fingerprint SHA-256
4. Verifica idempotência: mesmo fingerprint+tipo+data → retorna existente
5. Gera prompt versionado → chama provider → valida (5 camadas)
6. Falha em qualquer camada → fallback determinístico
7. Persiste ReportRun com todos os campos de auditoria
"""

import logging
from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.asset import Asset
from app.db.models.indicator_snapshot import IndicatorSnapshot
from app.db.models.report_run import ReportRun
from app.db.models.signal import Signal
from app.domain.reports import anthropic_provider as ap
from app.domain.reports import fallback_provider as fp
from app.domain.reports import output_renderer as renderer
from app.domain.reports import validators
from app.domain.reports.context_builder import build_context
from app.domain.reports.fingerprint import compute_fingerprint
from app.domain.reports.prompt import PROMPT_VERSION, build_prompt

logger = logging.getLogger(__name__)


def _get_provider() -> ap.AnthropicProvider:
    return ap.AnthropicProvider(
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        timeout=settings.llm_timeout_seconds,
        max_tokens=settings.llm_max_output_tokens,
    )


def generate_report(symbol: str, db: Session, report_type: str = "on_demand") -> ReportRun:
    """Gera ou retorna relatório idempotente para o ativo.

    Idempotência: mesmo asset_id + report_type + report_date + input_fingerprint
    → retorna o relatório existente sem nova chamada ao LLM.
    """
    asset = db.query(Asset).filter(Asset.symbol == symbol.upper()).first()
    if asset is None:
        raise ValueError(f"asset_not_found:{symbol}")

    signal = db.query(Signal).filter(Signal.asset_id == asset.id).order_by(Signal.id.desc()).first()
    if signal is None:
        raise ValueError(f"no_signal_available:{symbol}")

    snapshot = (
        db.query(IndicatorSnapshot)
        .filter(IndicatorSnapshot.asset_id == asset.id)
        .order_by(IndicatorSnapshot.id.desc())
        .first()
    )
    if snapshot is None:
        raise ValueError(f"no_snapshot_available:{symbol}")

    # Carrega relação para context_builder acessar asset.symbol/name via signal.asset
    if signal.asset is None:
        signal.asset = asset

    context = build_context(asset, signal, snapshot)
    fingerprint = compute_fingerprint(context)
    today = date.today()

    # Verificação de idempotência
    existing = (
        db.query(ReportRun)
        .filter(
            ReportRun.asset_id == asset.id,
            ReportRun.report_type == report_type,
            ReportRun.report_date == today,
            ReportRun.input_fingerprint == fingerprint,
        )
        .first()
    )
    if existing is not None:
        return existing

    # Tentativa de geração via LLM
    generated_text: str
    is_fallback = False
    generation_status = "generated"
    failure_reason: str | None = None
    model_name = settings.llm_model

    if settings.llm_api_key:
        try:
            prompt = build_prompt(context)
            provider = _get_provider()
            raw = provider.generate(prompt)
            result = validators.validate(raw, context)
            if result.ok:
                generated_text = renderer.render(result.parsed, context)
            else:
                logger.warning("Validação LLM falhou: %s", result.reason)
                failure_reason = f"validation_failed: {result.reason}"
                generated_text = fp.generate(context)
                is_fallback = True
                generation_status = "fallback"
                model_name = fp.FALLBACK_MODEL_NAME
        except Exception as exc:
            logger.error("Provider LLM falhou: %s", type(exc).__name__)
            failure_reason = f"provider_error: {type(exc).__name__}"
            generated_text = fp.generate(context)
            is_fallback = True
            generation_status = "fallback"
            model_name = fp.FALLBACK_MODEL_NAME
    else:
        logger.info("LLM_API_KEY não configurada — usando fallback determinístico")
        generated_text = fp.generate(context)
        is_fallback = True
        generation_status = "fallback"
        model_name = fp.FALLBACK_MODEL_NAME

    run = ReportRun(
        asset_id=asset.id,
        signal_id=signal.id,
        report_type=report_type,
        generated_text=generated_text,
        is_fallback=is_fallback,
        generation_status=generation_status,
        failure_reason=failure_reason,
        model_name=model_name,
        prompt_version=PROMPT_VERSION,
        data_quality=snapshot.status,
        input_snapshot_json=context,
        input_fingerprint=fingerprint,
        report_date=today,
    )

    try:
        db.add(run)
        db.commit()
        db.refresh(run)
    except IntegrityError:
        # Race condition: outro processo inseriu o mesmo relatório
        db.rollback()
        existing = (
            db.query(ReportRun)
            .filter(
                ReportRun.asset_id == asset.id,
                ReportRun.report_type == report_type,
                ReportRun.report_date == today,
                ReportRun.input_fingerprint == fingerprint,
            )
            .first()
        )
        if existing:
            return existing
        raise

    return run


def get_latest_report(symbol: str, db: Session) -> ReportRun | None:
    """Retorna o relatório mais recente do ativo, ou None se não existir."""
    asset = db.query(Asset).filter(Asset.symbol == symbol.upper()).first()
    if asset is None:
        return None
    return (
        db.query(ReportRun)
        .filter(ReportRun.asset_id == asset.id)
        .order_by(ReportRun.id.desc())
        .first()
    )
