from __future__ import annotations

from pathlib import Path

from agades_lwe_gym.evaluators.cascade import CascadeEvaluator


def evaluate(program_path: str) -> dict[str, float | int | str | bool | None]:
    result = CascadeEvaluator().evaluate_path(Path(program_path))
    return result.metrics

