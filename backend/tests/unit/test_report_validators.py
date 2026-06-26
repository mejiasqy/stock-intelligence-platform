"""Testes das 5 camadas de validação da saída do LLM."""

import json

from app.domain.reports.validators import validate

_VALID_CODES = {"price_above_sma_20", "rsi_in_bullish_range"}

_BASE_CONTEXT = {
    "score": 65.0,
    "rsi_14": 55.12,
    "sma_20": 28.50,
    "reason_codes": {
        "price_above_sma_20": {"value": True, "label": "Preço acima da SMA 20"},
        "rsi_in_bullish_range": {"value": False, "label": "RSI em zona saudável"},
    },
}

_VALID_JSON = json.dumps(
    {
        "summary": "Ativo com score de 65 pontos.",
        "positive_factors": [
            {"reason_code": "price_above_sma_20", "explanation": "Preço acima da SMA 20."}
        ],
        "attention_factors": [
            {"reason_code": "rsi_in_bullish_range", "explanation": "RSI não está na zona ideal."}
        ],
        "limitations": ["Dado parcial disponível."],
    }
)


def test_valid_output_passes_all_layers():
    result = validate(_VALID_JSON, _BASE_CONTEXT)
    assert result.ok is True
    assert result.parsed["summary"]


def test_prompt_contains_version():
    from app.domain.reports.prompt import PROMPT_VERSION, build_prompt

    ctx = {"score": 1.0, "reason_codes": {}}
    prompt = build_prompt(ctx)
    assert PROMPT_VERSION in prompt


def test_prompt_contains_guardrails():
    from app.domain.reports.prompt import build_prompt

    ctx = {"score": 1.0, "reason_codes": {}}
    prompt = build_prompt(ctx)
    assert "recomend" in prompt.lower() or "proibido" in prompt.lower()


def test_prompt_instructs_json_output():
    from app.domain.reports.prompt import build_prompt

    ctx = {"score": 1.0, "reason_codes": {}}
    prompt = build_prompt(ctx)
    assert "positive_factors" in prompt
    assert "attention_factors" in prompt


def test_invalid_json_fails():
    result = validate("not json {{{", _BASE_CONTEXT)
    assert result.ok is False
    assert "json_parse" in result.reason


def test_missing_section_fails():
    bad = json.dumps({"summary": "ok", "positive_factors": [], "attention_factors": []})
    result = validate(bad, _BASE_CONTEXT)
    assert result.ok is False
    assert "missing_sections" in result.reason


def test_unknown_reason_code_fails():
    bad = json.dumps(
        {
            "summary": "ok",
            "positive_factors": [{"reason_code": "invented_code", "explanation": "x"}],
            "attention_factors": [],
            "limitations": [],
        }
    )
    result = validate(bad, _BASE_CONTEXT)
    assert result.ok is False
    assert "unknown_reason_code" in result.reason


def test_prescriptive_term_fails():
    bad = json.dumps(
        {
            "summary": "Você deve comprar este ativo.",
            "positive_factors": [],
            "attention_factors": [],
            "limitations": [],
        }
    )
    result = validate(bad, _BASE_CONTEXT)
    assert result.ok is False


def test_external_reference_fails():
    bad = json.dumps(
        {
            "summary": "Segundo notícias do mercado, o ativo subiu.",
            "positive_factors": [],
            "attention_factors": [],
            "limitations": [],
        }
    )
    result = validate(bad, _BASE_CONTEXT)
    assert result.ok is False


def test_unauthorized_number_fails():
    bad = json.dumps(
        {
            "summary": "Ativo com score de 999 pontos.",
            "positive_factors": [],
            "attention_factors": [],
            "limitations": [],
        }
    )
    result = validate(bad, _BASE_CONTEXT)
    assert result.ok is False
    assert "unauthorized_number" in result.reason


def test_any_failure_returns_not_ok():
    result = validate("{}", _BASE_CONTEXT)
    assert result.ok is False
    assert result.reason
