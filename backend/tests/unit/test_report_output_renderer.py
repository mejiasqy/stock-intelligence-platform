"""Testes do output_renderer."""

from app.domain.reports.output_renderer import render

_VALIDATED = {
    "summary": "Ativo em tendência positiva.",
    "positive_factors": [
        {"reason_code": "price_above_sma_20", "explanation": "Preço acima da média."}
    ],
    "attention_factors": [{"reason_code": "rsi_in_bullish_range", "explanation": "RSI não ideal."}],
    "limitations": ["Dados parciais disponíveis."],
}

_CTX: dict = {}


def test_renderer_four_sections():
    text = render(_VALIDATED, _CTX)
    assert "## Resumo" in text
    assert "## Fatores positivos" in text
    assert "## Fatores de atenção" in text
    assert "## Limitações" in text


def test_renderer_uses_label():
    text = render(_VALIDATED, _CTX)
    # Deve usar o label humano do REASON_CODE_DEFS, não o código cru
    assert "Preço acima da SMA de 20 períodos" in text


def test_renderer_adds_disclaimer():
    text = render(_VALIDATED, _CTX)
    assert "educacion" in text.lower()
    assert "Aviso" in text
