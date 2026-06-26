"""Validação em 5 camadas da saída bruta do LLM.

Camada 1 — Parse JSON: a resposta deve ser JSON válido.
Camada 2 — Schema: 4 seções obrigatórias com tipos corretos.
Camada 3 — reason_codes: todo código citado deve existir no contexto.
Camada 4 — Guardrails: termos prescritivos/externos proibidos.
Camada 5 — Factual: números no texto devem existir no contexto ou ser constantes de período.

Qualquer falha → ValidationResult(ok=False). O serviço usa fallback determinístico.
A saída bruta do LLM nunca é persistida diretamente.
"""

import json
import re
from dataclasses import dataclass, field

from app.domain.reports.context_builder import KNOWN_PERIOD_CONSTANTS

# Termos prescritivos proibidos em qualquer campo de texto
_PROHIBITED_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bcomprar?\b",
        r"\bvender?\b",
        r"\bvenda\b",
        r"\brecomend[ao]\b",
        r"\brecomendamos\b",
        r"\bgarantim?os?\b",
        r"\bgarantia\b",
        r"\bvai subir\b",
        r"\bvai cair\b",
        r"\blucro garantido\b",
        r"\binvista\b",
        r"\baplicar?\b",
        r"\bvocê deve\b",
        r"\bprevisão é\b",
        r"\bcerteza\b",
        r"\brentabilidade futura\b",
        r"\bnotícia[s]?\b",
        r"\bevento[s]?\b",
        r"\bsegundo\s+\w+\s+\(",  # "segundo Fonte ("
    ]
]

# Extrai números decimais de um texto
_NUMBER_RE = re.compile(r"\b\d+(?:[.,]\d+)?\b")

_REQUIRED_KEYS = {"summary", "positive_factors", "attention_factors", "limitations"}


@dataclass
class ValidationResult:
    ok: bool
    parsed: dict = field(default_factory=dict)
    reason: str = ""


def _collect_context_numbers(context: dict) -> frozenset[float]:
    """Extrai todos os valores numéricos do contexto, arredondados a 2 casas."""
    nums: set[float] = set(KNOWN_PERIOD_CONSTANTS)
    for v in context.values():
        if isinstance(v, (int, float)):
            nums.add(round(float(v), 2))
        elif isinstance(v, dict):
            for vv in v.values():
                if isinstance(vv, (int, float)):
                    nums.add(round(float(vv), 2))
    return frozenset(nums)


def _extract_text_fields(parsed: dict) -> list[str]:
    """Coleta todos os campos de texto da resposta para verificação."""
    texts: list[str] = []
    if isinstance(parsed.get("summary"), str):
        texts.append(parsed["summary"])
    for group_key in ("positive_factors", "attention_factors"):
        for item in parsed.get(group_key) or []:
            if isinstance(item, dict) and isinstance(item.get("explanation"), str):
                texts.append(item["explanation"])
    for lim in parsed.get("limitations") or []:
        if isinstance(lim, str):
            texts.append(lim)
    return texts


def validate(raw_response: str, context: dict) -> ValidationResult:
    """Executa as 5 camadas de validação e retorna o resultado."""

    # Camada 1 — Parse JSON
    try:
        parsed = json.loads(raw_response.strip())
    except (json.JSONDecodeError, ValueError) as exc:
        return ValidationResult(ok=False, reason=f"json_parse_error: {exc}")

    if not isinstance(parsed, dict):
        return ValidationResult(ok=False, reason="response_not_object")

    # Camada 2 — Schema obrigatório
    missing = _REQUIRED_KEYS - parsed.keys()
    if missing:
        return ValidationResult(ok=False, reason=f"missing_sections: {missing}")

    if not isinstance(parsed.get("summary"), str) or not parsed["summary"].strip():
        return ValidationResult(ok=False, reason="summary_empty_or_wrong_type")

    for group_key in ("positive_factors", "attention_factors"):
        group = parsed.get(group_key)
        if not isinstance(group, list):
            return ValidationResult(ok=False, reason=f"{group_key}_not_list")
        for item in group:
            if not isinstance(item, dict) or "reason_code" not in item or "explanation" not in item:
                return ValidationResult(ok=False, reason=f"{group_key}_item_invalid")

    if not isinstance(parsed.get("limitations"), list):
        return ValidationResult(ok=False, reason="limitations_not_list")

    # Camada 3 — reason_codes válidos
    valid_codes: set[str] = set(context.get("reason_codes", {}).keys())
    for group_key in ("positive_factors", "attention_factors"):
        for item in parsed.get(group_key, []):
            code = item.get("reason_code", "")
            if code not in valid_codes:
                return ValidationResult(ok=False, reason=f"unknown_reason_code: {code!r}")

    # Camada 4 — Guardrails: termos proibidos
    all_texts = _extract_text_fields(parsed)
    for text in all_texts:
        for pattern in _PROHIBITED_PATTERNS:
            if pattern.search(text):
                return ValidationResult(ok=False, reason=f"prohibited_pattern: {pattern.pattern!r}")

    # Camada 5 — Factual: números no texto devem existir no contexto
    allowed_numbers = _collect_context_numbers(context)
    for text in all_texts:
        for match in _NUMBER_RE.finditer(text):
            raw_num = match.group().replace(",", ".")
            try:
                num = round(float(raw_num), 2)
            except ValueError:
                continue
            if num not in allowed_numbers:
                return ValidationResult(
                    ok=False, reason=f"unauthorized_number: {num} not in context"
                )

    return ValidationResult(ok=True, parsed=parsed)
