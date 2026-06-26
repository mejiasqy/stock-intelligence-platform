"""Envio de alertas via Telegram Bot API usando httpx síncrono.

Regras de segurança:
- bot_token e chat_id nunca são logados inteiramente.
- Em dry_run=True, nenhuma chamada de rede é feita.
- O payload sanitizado (sem token) é o que vai para alert_log.
"""

import logging

import httpx

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org"


def send_alert(
    *,
    payload: dict,
    bot_token: str,
    chat_id: str,
    dry_run: bool,
) -> str:
    """Envia ou simula envio de alerta Telegram.

    Retorna delivery_status: 'sent' | 'dry_run' | 'failed'.
    O bot_token aparece apenas na URL da requisição — nunca em logs.
    """
    if dry_run:
        # Loga apenas dados não-sensíveis do payload
        logger.info(
            "ALERTA DRY-RUN rule=%s asset=%s",
            payload.get("rule"),
            payload.get("asset_symbol"),
        )
        return "dry_run"

    message = _format_message(payload)
    url = f"{_TELEGRAM_API}/bot{bot_token}/sendMessage"

    try:
        response = httpx.post(
            url,
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
            timeout=10.0,
        )
        response.raise_for_status()
        logger.info(
            "Alerta Telegram enviado rule=%s asset=%s",
            payload.get("rule"),
            payload.get("asset_symbol"),
        )
        return "sent"
    except Exception as exc:
        # Loga apenas o tipo de erro — nunca o token ou chat_id
        logger.error("Falha ao enviar alerta Telegram: %s", type(exc).__name__)
        return "failed"


def _format_message(payload: dict) -> str:
    rule = payload.get("rule", "")
    symbol = payload.get("asset_symbol", "?")

    if rule == "signal_change":
        prev = payload.get("previous_signal", "?")
        curr = payload.get("current_signal", "?")
        score = payload.get("score")
        score_str = f"{score:.1f}" if isinstance(score, float) else "?"
        return (
            f"*Stock Intelligence* — Mudança de sinal\n"
            f"Ativo: `{symbol}`\n"
            f"Sinal anterior: {prev} → Sinal atual: *{curr}*\n"
            f"Score: {score_str}\n"
            f"_Apenas para fins analíticos e educacionais._"
        )

    if rule in ("score_high", "score_low"):
        score = payload.get("score", "?")
        threshold = payload.get("threshold", "?")
        label = "alto" if rule == "score_high" else "baixo"
        return (
            f"*Stock Intelligence* — Score {label}\n"
            f"Ativo: `{symbol}`\n"
            f"Score: *{score}* (limiar: {threshold})\n"
            f"_Apenas para fins analíticos e educacionais._"
        )

    return f"*Stock Intelligence* — Alerta: {rule} para {symbol}"
