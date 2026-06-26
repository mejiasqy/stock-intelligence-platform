"""Testes do fallback determinístico."""

from app.domain.reports.fallback_provider import FALLBACK_MODEL_NAME, generate

_CTX = {
    "asset_symbol": "VALE3.SA",
    "signal_type": "bearish",
    "score": 35.0,
    "data_quality": "ok",
    "candles_used": 250,
    "insufficient_fields": {},
    "reason_codes": {
        "price_above_sma_20": {"value": True, "label": "Preço acima da SMA de 20 períodos"},
        "rsi_in_bullish_range": {"value": False, "label": "RSI em zona saudável (40–70)"},
    },
}


def test_fallback_has_four_sections():
    text = generate(_CTX)
    assert "## Resumo" in text
    assert "## Fatores positivos" in text
    assert "## Fatores de atenção" in text
    assert "## Limitações" in text


def test_fallback_uses_human_labels():
    text = generate(_CTX)
    assert "Preço acima da SMA de 20 períodos" in text
    assert "RSI em zona saudável" in text


def test_fallback_has_disclaimer():
    text = generate(_CTX)
    assert "educacion" in text.lower()
    assert "recomendação" in text.lower()


def test_fallback_model_name():
    assert FALLBACK_MODEL_NAME == "fallback/1.0.0"


def test_fallback_null_context_safe():
    ctx = {
        "asset_symbol": "X",
        "signal_type": "neutral",
        "score": None,
        "data_quality": "insufficient_data",
        "candles_used": 0,
        "insufficient_fields": {},
        "reason_codes": {},
    }
    text = generate(ctx)
    assert "## Resumo" in text
