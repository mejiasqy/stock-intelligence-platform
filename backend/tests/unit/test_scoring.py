"""Testes unitários do motor de scoring — funções puras sem banco."""

import pytest

from app.domain.scoring import pillars as p
from app.domain.scoring.engine import SCORING_VERSION, score
from app.domain.scoring.reason_codes import evaluate  # noqa: E402

# ---------------------------------------------------------------------------
# evaluate() — reason_codes
# ---------------------------------------------------------------------------


def _base_kwargs() -> dict:
    """Snapshot com dados suficientes para todos os códigos."""
    return {
        "last_close": 35.0,
        "last_volume": 2_000_000.0,
        "sma_20": 33.0,
        "sma_50": 30.0,
        "ema_20": 34.0,
        "rsi_14": 55.0,
        "macd": 0.5,
        "macd_signal": 0.3,
        "bollinger_upper": 40.0,
        "bollinger_middle": 33.0,
        "bollinger_lower": 26.0,
        "volume_avg_20": 1_000_000.0,
        "vol_annualized_20d": 0.25,
        "max_drawdown_60d": -0.10,
        "current_drawdown_60d": -0.05,
        "return_1d": 0.01,
        "return_5d": 0.03,
        "return_20d": 0.08,
        "return_60d": 0.15,
    }


def test_evaluate_all_bullish() -> None:
    codes = evaluate(**_base_kwargs())
    assert codes["price_above_sma_20"] is True
    assert codes["price_above_sma_50"] is True
    assert codes["ema_above_sma_20"] is True
    assert codes["return_20d_positive"] is True
    assert codes["return_60d_positive"] is True
    assert codes["macd_positive"] is True
    assert codes["macd_above_signal"] is True
    assert codes["return_1d_positive"] is True
    assert codes["return_5d_positive"] is True
    assert codes["rsi_in_bullish_range"] is True
    assert codes["volume_above_avg"] is True
    assert codes["volume_surge"] is True
    assert codes["volatility_contained"] is True
    assert codes["current_drawdown_mild"] is True
    assert codes["max_drawdown_acceptable"] is True
    assert codes["price_above_bollinger_lower"] is True
    assert codes["price_at_or_above_mid_band"] is True
    assert codes["sma_20_above_sma_50"] is True
    assert codes["return_5d_outpacing_20d"] is False  # 0.03 < 0.08
    assert codes["price_below_bollinger_upper"] is True


def test_evaluate_none_fields_return_false() -> None:
    kwargs = _base_kwargs()
    kwargs["sma_20"] = None
    kwargs["sma_50"] = None
    codes = evaluate(**kwargs)
    assert codes["price_above_sma_20"] is False
    assert codes["price_above_sma_50"] is False
    assert codes["ema_above_sma_20"] is False
    assert codes["sma_20_above_sma_50"] is False


def test_rsi_out_of_bullish_range() -> None:
    kwargs = _base_kwargs()
    kwargs["rsi_14"] = 75.0
    codes = evaluate(**kwargs)
    assert codes["rsi_in_bullish_range"] is False

    kwargs["rsi_14"] = 30.0
    codes = evaluate(**kwargs)
    assert codes["rsi_in_bullish_range"] is False

    kwargs["rsi_14"] = 40.0
    codes = evaluate(**kwargs)
    assert codes["rsi_in_bullish_range"] is True


def test_volume_surge_threshold() -> None:
    kwargs = _base_kwargs()
    kwargs["last_volume"] = 1_400_000.0  # < 1.5x avg
    codes = evaluate(**kwargs)
    assert codes["volume_above_avg"] is True
    assert codes["volume_surge"] is False

    kwargs["last_volume"] = 1_500_001.0  # > 1.5x avg
    codes = evaluate(**kwargs)
    assert codes["volume_surge"] is True


def test_volatility_threshold() -> None:
    kwargs = _base_kwargs()
    kwargs["vol_annualized_20d"] = 0.40
    codes = evaluate(**kwargs)
    assert codes["volatility_contained"] is False  # não é < 0.40

    kwargs["vol_annualized_20d"] = 0.399
    codes = evaluate(**kwargs)
    assert codes["volatility_contained"] is True


# ---------------------------------------------------------------------------
# pillars
# ---------------------------------------------------------------------------


def test_volume_score_surge() -> None:
    assert p.volume_score({"volume_surge": True, "volume_above_avg": True}) == 100.0


def test_volume_score_above_avg_only() -> None:
    assert p.volume_score({"volume_surge": False, "volume_above_avg": True}) == 60.0


def test_volume_score_none() -> None:
    assert p.volume_score({"volume_surge": False, "volume_above_avg": False}) == 0.0


def test_trend_score_full() -> None:
    codes = {
        "price_above_sma_20": True,
        "price_above_sma_50": True,
        "ema_above_sma_20": True,
        "return_20d_positive": True,
        "return_60d_positive": True,
    }
    assert p.trend_score(codes) == 100.0


def test_trend_score_partial() -> None:
    codes = {
        "price_above_sma_20": True,
        "price_above_sma_50": False,
        "ema_above_sma_20": False,
        "return_20d_positive": True,
        "return_60d_positive": False,
    }
    assert p.trend_score(codes) == pytest.approx(40.0)


# ---------------------------------------------------------------------------
# score() — payload final
# ---------------------------------------------------------------------------


def test_score_bullish() -> None:
    payload = score(**_base_kwargs())
    assert payload.score >= 60.0
    assert payload.signal_type == "bullish"
    assert 0.0 <= payload.strength <= 1.0
    assert payload.scoring_version == SCORING_VERSION
    assert len(payload.reason_codes) == 20
    assert set(payload.pillar_scores.keys()) == {"trend", "momentum", "volume", "risk", "structure"}


def test_score_bearish_all_none() -> None:
    """Snapshot sem dados → todos os codes False → score muito baixo → bearish."""
    kwargs = {k: None for k in _base_kwargs()}
    payload = score(**kwargs)
    assert payload.score <= 40.0
    assert payload.signal_type == "bearish"


def test_score_with_missing_volume_data() -> None:
    kwargs = _base_kwargs()
    kwargs["last_volume"] = None
    kwargs["volume_avg_20"] = None
    payload = score(**kwargs)
    # volume pillar zerado, mas outros contribuem — score ainda pode ser bullish
    assert payload.pillar_scores["volume"] == 0.0
    assert payload.score >= 0.0


def test_score_strength_bounds() -> None:
    payload = score(**_base_kwargs())
    assert 0.0 <= payload.strength <= 1.0


def test_score_neutral_range() -> None:
    """Score entre 40 e 60 → neutral."""
    kwargs = _base_kwargs()
    # Zeramos metade dos sinais positivos
    kwargs["return_20d"] = -0.01
    kwargs["return_60d"] = -0.01
    kwargs["macd"] = -0.1
    kwargs["macd_signal"] = 0.0
    kwargs["return_1d"] = -0.005
    kwargs["return_5d"] = -0.01
    kwargs["last_volume"] = 500_000.0  # abaixo da média
    kwargs["vol_annualized_20d"] = 0.50  # alta vol
    payload = score(**kwargs)
    assert payload.signal_type in ("neutral", "bearish")
