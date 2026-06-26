"""Regras de alerta: SignalChangeRule, ScoreHighRule, ScoreLowRule.

Semântica de primeira observação (D-ALERT-2 / D-ALERT-3):
- Se alert_state não existe para asset_id + rule_key: gravar estado atual, NÃO disparar.
- A partir da segunda observação: comparar e decidir disparo.

O payload retornado é sanitizado — nunca contém token, chat_id ou segredos.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.db.models.alert_state import AlertState
    from app.db.models.signal import Signal


@dataclass
class RuleResult:
    should_fire: bool
    payload: dict  # sanitizado, sem segredos
    new_state_value: dict  # valor a gravar/atualizar em alert_state


@runtime_checkable
class AlertRule(Protocol):
    key: str

    def evaluate(self, signal: Signal, state: AlertState | None) -> RuleResult: ...


class SignalChangeRule:
    key = "signal_change"

    def evaluate(self, signal: Signal, state: AlertState | None) -> RuleResult:
        current = signal.signal_type
        new_state = {"signal_type": current}
        payload = {
            "rule": self.key,
            "asset_symbol": signal.asset.symbol if signal.asset else str(signal.asset_id),
            "previous_signal": None,
            "current_signal": current,
            "score": float(signal.score) if signal.score is not None else None,
        }

        if state is None:
            # Primeira observação: gravar estado, não disparar
            return RuleResult(should_fire=False, payload=payload, new_state_value=new_state)

        previous = (state.last_observed_value_json or {}).get("signal_type")
        payload["previous_signal"] = previous

        if previous == current:
            return RuleResult(should_fire=False, payload=payload, new_state_value=new_state)

        return RuleResult(should_fire=True, payload=payload, new_state_value=new_state)


class ScoreHighRule:
    key = "score_high"

    def __init__(self, threshold: float) -> None:
        self._threshold = threshold

    def evaluate(self, signal: Signal, state: AlertState | None) -> RuleResult:
        score = float(signal.score) if signal.score is not None else 0.0
        new_state = {"score": score}
        payload = {
            "rule": self.key,
            "asset_symbol": signal.asset.symbol if signal.asset else str(signal.asset_id),
            "score": score,
            "threshold": self._threshold,
            "signal_type": signal.signal_type,
        }

        if state is None:
            return RuleResult(should_fire=False, payload=payload, new_state_value=new_state)

        fires = score >= self._threshold
        return RuleResult(should_fire=fires, payload=payload, new_state_value=new_state)


class ScoreLowRule:
    key = "score_low"

    def __init__(self, threshold: float) -> None:
        self._threshold = threshold

    def evaluate(self, signal: Signal, state: AlertState | None) -> RuleResult:
        score = float(signal.score) if signal.score is not None else 0.0
        new_state = {"score": score}
        payload = {
            "rule": self.key,
            "asset_symbol": signal.asset.symbol if signal.asset else str(signal.asset_id),
            "score": score,
            "threshold": self._threshold,
            "signal_type": signal.signal_type,
        }

        if state is None:
            return RuleResult(should_fire=False, payload=payload, new_state_value=new_state)

        fires = score <= self._threshold
        return RuleResult(should_fire=fires, payload=payload, new_state_value=new_state)
