from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

PEDAGOGICAL_REWARD_REPORT_SCHEMA = "agades.pqc.rl.pedagogical_reward.v1"
DEFAULT_SPIKE_BETA = 5.0
DEFAULT_SPIKE_LAMBDA = 1.0
DEFAULT_SURPRISAL_KAPPA = 2.0
DEFAULT_SURPRISAL_GAMMA = -4.0


def spike_aware_learnability_score(
    surprise_gaps: Sequence[float],
    *,
    beta: float = DEFAULT_SPIKE_BETA,
    lambda_: float = DEFAULT_SPIKE_LAMBDA,
) -> float:
    gaps = _finite_sequence(surprise_gaps, label="surprise_gaps")
    if not gaps:
        raise ValueError("surprise_gaps must not be empty")
    if any(gap < 0.0 for gap in gaps):
        raise ValueError("surprise_gaps must be non-negative")
    if beta <= 0.0 or not math.isfinite(beta):
        raise ValueError("beta must be a finite positive number")
    if lambda_ < 0.0 or not math.isfinite(lambda_):
        raise ValueError("lambda_ must be a finite non-negative number")

    scaled = [beta * gap for gap in gaps]
    max_scaled = max(scaled)
    log_mean_exp = max_scaled + math.log(
        sum(math.exp(value - max_scaled) for value in scaled) / len(scaled)
    )
    return math.exp(-(lambda_ / beta) * log_mean_exp)


def surprisal_gated_token_weights(
    student_token_logprobs: Sequence[float],
    *,
    kappa: float = DEFAULT_SURPRISAL_KAPPA,
    gamma: float = DEFAULT_SURPRISAL_GAMMA,
) -> list[float]:
    logprobs = _finite_sequence(
        student_token_logprobs,
        label="student_token_logprobs",
    )
    if kappa <= 0.0 or not math.isfinite(kappa):
        raise ValueError("kappa must be a finite positive number")
    if not math.isfinite(gamma):
        raise ValueError("gamma must be finite")
    return [_stable_sigmoid(kappa * (logprob - gamma)) for logprob in logprobs]


def build_pedagogical_reward_report(
    base_reward: float,
    pedagogical_signals: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if base_reward < 0.0 or base_reward > 1.0 or not math.isfinite(base_reward):
        raise ValueError("base_reward must be finite and in [0, 1]")
    if pedagogical_signals is None:
        return _report(
            base_reward=base_reward,
            final_reward=base_reward,
            applied=False,
            learnability_score=None,
            assimilation_weights=[],
            signal_error=None,
        )
    if not isinstance(pedagogical_signals, Mapping):
        return _error_report(base_reward, "pedagogical_signals must be a mapping")

    try:
        surprise_gaps = pedagogical_signals.get("surprise_gaps")
        if surprise_gaps is None:
            raise ValueError("pedagogical_signals.surprise_gaps is required")
        learnability_score = spike_aware_learnability_score(surprise_gaps)
        token_logprobs = pedagogical_signals.get("student_token_logprobs", [])
        assimilation_weights = surprisal_gated_token_weights(token_logprobs)
    except (TypeError, ValueError) as exc:
        return _error_report(base_reward, str(exc))

    final_reward = base_reward * learnability_score
    return _report(
        base_reward=base_reward,
        final_reward=final_reward,
        applied=True,
        learnability_score=learnability_score,
        assimilation_weights=assimilation_weights,
        signal_error=None,
    )


def _report(
    *,
    base_reward: float,
    final_reward: float,
    applied: bool,
    learnability_score: float | None,
    assimilation_weights: Sequence[float],
    signal_error: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": PEDAGOGICAL_REWARD_REPORT_SCHEMA,
        "applied": applied,
        "base_reward": base_reward,
        "learnability_score": learnability_score,
        "final_reward": final_reward,
        "raw_private_signals_included": False,
        "private_student_signals_required_for_application": True,
        "assimilation_weights": _weight_summary(assimilation_weights),
        "signal_error": signal_error,
    }


def _error_report(base_reward: float, signal_error: str) -> dict[str, Any]:
    return _report(
        base_reward=base_reward,
        final_reward=0.0,
        applied=False,
        learnability_score=None,
        assimilation_weights=[],
        signal_error=signal_error,
    )


def _weight_summary(weights: Sequence[float]) -> dict[str, float | int | None]:
    if not weights:
        return {"count": 0, "min": None, "max": None, "mean": None}
    return {
        "count": len(weights),
        "min": min(weights),
        "max": max(weights),
        "mean": sum(weights) / len(weights),
    }


def _finite_sequence(value: Sequence[float], *, label: str) -> list[float]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"{label} must be a sequence of numbers")
    numbers = [float(item) for item in value]
    if any(not math.isfinite(item) for item in numbers):
        raise ValueError(f"{label} values must be finite")
    return numbers


def _stable_sigmoid(value: float) -> float:
    if value >= 0.0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)
