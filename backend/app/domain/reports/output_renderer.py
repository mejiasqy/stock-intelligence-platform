"""Converte o JSON validado do LLM em texto final em português.

Responsabilidades:
- Montar as 4 seções com labels humanos dos reason_codes
- Acrescentar disclaimer educacional obrigatório
- Nunca expor dados brutos ou técnicos do sistema
"""

from app.domain.scoring.reason_codes import REASON_CODE_DEFS

_LABEL_BY_CODE: dict[str, str] = {d.code: d.description for d in REASON_CODE_DEFS}

_DISCLAIMER = (
    "\n---\n"
    "**Aviso:** Este relatório é gerado automaticamente para fins educacionais e analíticos. "
    "Não constitui recomendação de investimento, consultoria financeira ou garantia de resultado. "
    "Decisões de investimento devem ser tomadas com base em análise própria e orientação de "
    "profissionais habilitados."
)


def render(validated_json: dict, context: dict) -> str:  # noqa: ARG001
    """Constrói o texto final a partir do JSON validado.

    O parâmetro `context` é recebido para consistência com a assinatura
    esperada pelo serviço; não é usado na renderização (os dados já estão
    no JSON validado via reason_codes e explanations).
    """
    lines: list[str] = []

    # Resumo
    lines.append("## Resumo")
    lines.append(validated_json.get("summary", "").strip())
    lines.append("")

    # Fatores positivos
    lines.append("## Fatores positivos")
    positive = validated_json.get("positive_factors", [])
    if positive:
        for item in positive:
            code = item.get("reason_code", "")
            label = _LABEL_BY_CODE.get(code, code)
            explanation = item.get("explanation", "").strip()
            lines.append(f"- **{label}**: {explanation}")
    else:
        lines.append("- Nenhum fator positivo identificado nos dados disponíveis.")
    lines.append("")

    # Fatores de atenção
    lines.append("## Fatores de atenção")
    attention = validated_json.get("attention_factors", [])
    if attention:
        for item in attention:
            code = item.get("reason_code", "")
            label = _LABEL_BY_CODE.get(code, code)
            explanation = item.get("explanation", "").strip()
            lines.append(f"- **{label}**: {explanation}")
    else:
        lines.append("- Nenhum fator de atenção identificado nos dados disponíveis.")
    lines.append("")

    # Limitações
    lines.append("## Limitações")
    limitations = validated_json.get("limitations", [])
    if limitations:
        for lim in limitations:
            lines.append(f"- {lim.strip()}")
    else:
        lines.append("- Nenhuma limitação adicional identificada.")

    lines.append(_DISCLAIMER)
    return "\n".join(lines)
