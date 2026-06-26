"""Testes das regras de alerta."""

from unittest.mock import MagicMock

from app.domain.alerts.rules import ScoreHighRule, ScoreLowRule, SignalChangeRule


def _sig(signal_type="bullish", score=75.0):
    s = MagicMock()
    s.signal_type = signal_type
    s.score = score
    s.asset_id = 1
    s.asset = MagicMock()
    s.asset.symbol = "PETR4.SA"
    return s


def _state(signal_type=None, score=None):
    st = MagicMock()
    if signal_type is not None:
        st.last_observed_value_json = {"signal_type": signal_type}
    elif score is not None:
        st.last_observed_value_json = {"score": score}
    return st


# SignalChangeRule
def test_signal_change_first_observation_no_fire():
    r = SignalChangeRule().evaluate(_sig("bullish"), None)
    assert r.should_fire is False
    assert r.new_state_value == {"signal_type": "bullish"}


def test_signal_change_same_signal_no_fire():
    r = SignalChangeRule().evaluate(_sig("bullish"), _state(signal_type="bullish"))
    assert r.should_fire is False


def test_signal_change_different_signal_fires():
    r = SignalChangeRule().evaluate(_sig("bearish"), _state(signal_type="bullish"))
    assert r.should_fire is True
    assert r.payload["previous_signal"] == "bullish"
    assert r.payload["current_signal"] == "bearish"


# ScoreHighRule
def test_score_high_first_observation_no_fire():
    r = ScoreHighRule(70.0).evaluate(_sig(score=80.0), None)
    assert r.should_fire is False


def test_score_high_above_threshold():
    r = ScoreHighRule(70.0).evaluate(_sig(score=80.0), _state(score=80.0))
    assert r.should_fire is True


def test_score_high_below_threshold():
    r = ScoreHighRule(70.0).evaluate(_sig(score=50.0), _state(score=50.0))
    assert r.should_fire is False


# ScoreLowRule
def test_score_low_first_observation_no_fire():
    r = ScoreLowRule(25.0).evaluate(_sig(score=20.0), None)
    assert r.should_fire is False


def test_score_low_below_threshold():
    r = ScoreLowRule(25.0).evaluate(_sig(score=20.0), _state(score=20.0))
    assert r.should_fire is True


def test_rule_payload_no_secrets():
    import json

    r = SignalChangeRule().evaluate(_sig("bearish"), _state(signal_type="bullish"))
    payload_str = json.dumps(r.payload).lower()
    for secret in ("token", "api_key", "chat_id", "password"):
        assert secret not in payload_str
