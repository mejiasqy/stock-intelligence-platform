"""Testes do context_builder e fingerprint."""

import hashlib
import json
from unittest.mock import MagicMock

from app.domain.reports.context_builder import build_context
from app.domain.reports.fingerprint import compute_fingerprint

_SECRETS = ["llm_api_key", "telegram_bot_token", "telegram_chat_id", "api_secret_key"]


def _make_asset(symbol="PETR4.SA", name="Petrobras"):
    a = MagicMock()
    a.symbol = symbol
    a.name = name
    return a


def _make_signal(signal_type="bullish", score=65.0, strategy_version="1.0.0"):
    s = MagicMock()
    s.signal_type = signal_type
    s.score = score
    s.strength = 0.3
    s.strategy_version = strategy_version
    s.calculated_at = None
    s.reason_codes = {"price_above_sma_20": True, "rsi_in_bullish_range": False}
    s.pillar_scores = {"trend": 20.0, "momentum": 15.0}
    s.asset = None
    s.asset_id = 1
    return s


def _make_snapshot(status="ok", candles_used=250):
    sn = MagicMock()
    sn.status = status
    sn.candles_used = candles_used
    sn.calculation_version = "1.0.0"
    sn.calculated_at = None
    sn.insufficient_fields = {}
    for attr in [
        "last_close",
        "sma_20",
        "sma_50",
        "ema_20",
        "rsi_14",
        "macd",
        "macd_signal",
        "macd_histogram",
        "bollinger_upper",
        "bollinger_middle",
        "bollinger_lower",
        "volume_avg_20",
        "last_volume",
        "vol_annualized_20d",
        "max_drawdown_60d",
        "current_drawdown_60d",
        "return_1d",
        "return_5d",
        "return_20d",
        "return_60d",
    ]:
        setattr(sn, attr, 10.0)
    return sn


def test_context_builder_full_snapshot():
    ctx = build_context(_make_asset(), _make_signal(), _make_snapshot())
    assert ctx["asset_symbol"] == "PETR4.SA"
    assert ctx["signal_type"] == "bullish"
    assert "reason_codes" in ctx
    assert "price_above_sma_20" in ctx["reason_codes"]
    assert ctx["reason_codes"]["price_above_sma_20"]["value"] is True
    assert "label" in ctx["reason_codes"]["price_above_sma_20"]


def test_context_builder_null_fields():
    sn = _make_snapshot()
    sn.rsi_14 = None
    sn.macd = None
    ctx = build_context(_make_asset(), _make_signal(), sn)
    assert ctx["rsi_14"] is None
    assert ctx["macd"] is None


def test_context_no_secrets():
    ctx = build_context(_make_asset(), _make_signal(), _make_snapshot())
    ctx_str = json.dumps(ctx).lower()
    for secret in _SECRETS:
        assert secret not in ctx_str


def test_fingerprint_is_sha256_of_canonical_json():
    ctx = {"b": 2, "a": 1}
    fp = compute_fingerprint(ctx)
    canonical = json.dumps(ctx, sort_keys=True, ensure_ascii=True, default=str)
    expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    assert fp == expected
    assert len(fp) == 64


def test_fingerprint_deterministic():
    ctx = build_context(_make_asset(), _make_signal(), _make_snapshot())
    assert compute_fingerprint(ctx) == compute_fingerprint(ctx)


def test_fingerprint_changes_with_score():
    s1 = _make_signal(score=65.0)
    s2 = _make_signal(score=72.0)
    sn = _make_snapshot()
    fp1 = compute_fingerprint(build_context(_make_asset(), s1, sn))
    fp2 = compute_fingerprint(build_context(_make_asset(), s2, sn))
    assert fp1 != fp2


def test_fingerprint_input_no_secrets():
    ctx = build_context(_make_asset(), _make_signal(), _make_snapshot())
    canonical = json.dumps(ctx, sort_keys=True, ensure_ascii=True, default=str).lower()
    for secret in _SECRETS:
        assert secret not in canonical
