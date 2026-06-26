"""Provider de fallback determinístico.

Usado quando o provider LLM falha, expira ou a saída não passa na validação.
Depende apenas do contexto estruturado — sem chamada de rede.
Usa labels humanos de REASON_CODE_DEFS, nunca chaves técnicas cruas.
Sempre inclui disclaimer educacional.
"""

FALLBACK_MODEL_NAME = "fallback/1.0.0"

_DISCLAIMER = (
    "\n---\n"
    "**Aviso:** Este relatório é gerado automaticamente para fins educacionais e analíticos. "
    "Não constitui recomendação de investimento, consultoria financeira ou garantia de resultado. "
    "Decisões de investimento devem ser tomadas com base em análise própria e orientação de "
    "profissionais habilitados."
)

_SIGNAL_LABELS = {
    "bullish": "sinal positivo",
    "bearish": "sinal negativo",
    "neutral": "sinal neutro",
}

_DATA_QUALITY_LABELS = {
    "ok": "completo",
    "partial": "parcial — alguns indicadores indisponíveis",
    "insufficient_data": "insuficiente — dados históricos abaixo do mínimo necessário",
}


def generate(context: dict) -> str:
    """Gera relatório determinístico a partir do contexto estruturado."""
    symbol: str = context.get("asset_symbol", "Ativo desconhecido")
    signal_type: str = context.get("signal_type", "neutral")
    score: object = context.get("score")
    data_quality: str = context.get("data_quality", "ok")
    candles: object = context.get("candles_used")
    reason_codes: dict = context.get("reason_codes", {})

    signal_label = _SIGNAL_LABELS.get(signal_type, signal_type)
    quality_label = _DATA_QUALITY_LABELS.get(data_quality, data_quality)

    score_str = f"{score:.1f}" if isinstance(score, (int, float)) else "indisponível"
    candles_str = str(candles) if candles is not None else "desconhecido"

    positive = [
        info["label"]
        for code, info in reason_codes.items()
        if isinstance(info, dict) and info.get("value") is True
    ]
    attention = [
        info["label"]
        for code, info in reason_codes.items()
        if isinstance(info, dict) and info.get("value") is False
    ]

    lines: list[str] = []

    lines.append("## Resumo")
    lines.append(
        f"{symbol} apresenta {signal_label} com score técnico de {score_str}. "
        f"A análise utilizou {candles_str} candles com dados {quality_label}."
    )
    lines.append("")

    lines.append("## Fatores positivos")
    if positive:
        for label in positive:
            lines.append(f"- {label}")
    else:
        lines.append("- Nenhum critério positivo atendido nos dados disponíveis.")
    lines.append("")

    lines.append("## Fatores de atenção")
    if attention:
        for label in attention:
            lines.append(f"- {label}")
    else:
        lines.append("- Nenhum critério de atenção identificado.")
    lines.append("")

    lines.append("## Limitações")
    insufficient: dict = context.get("insufficient_fields", {}) or {}
    if insufficient:
        items = ", ".join(f"{k} (mín. {v})" for k, v in list(insufficient.items())[:5])
        lines.append(f"- Indicadores indisponíveis por dados insuficientes: {items}.")
    if data_quality != "ok":
        lines.append(f"- Qualidade dos dados: {quality_label}.")
    lines.append(
        "- Relatório gerado por método determinístico (sem modelo de linguagem). "
        "Análise baseada exclusivamente em indicadores técnicos calculados pelo sistema."
    )

    lines.append(_DISCLAIMER)
    return "\n".join(lines)
