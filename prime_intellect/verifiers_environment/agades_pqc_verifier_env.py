from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.integrations.task_metadata import (
    normalize_task_metadata,
    task_metadata_for_plan,
)
from agades_pqc_gym.rl.environment import score_attack_plan_candidate

PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_DIR / "data"
TASK_PLAN_PATHS = sorted(DATA_DIR.glob("*.json"))
SYSTEM_PROMPT = (
    "You submit JSON AttackPlan candidates for Agades PQC Gym. "
    "Return only a single AttackPlan JSON object. Do not submit Python, shell, "
    "network requests, exploit chains, or live-target instructions."
)


def build_dataset_rows(num_examples: int | None = None) -> list[dict[str, Any]]:
    rows = [_row_for_plan(path) for path in TASK_PLAN_PATHS]
    if num_examples is None or num_examples < 0:
        return rows
    return rows[:num_examples]


def score_attack_plan_completion(
    completion: list[dict[str, Any]],
    *,
    info: dict[str, Any] | str | None = None,
    require_info: bool = False,
) -> float:
    candidate = _single_json_object_text(_last_content(completion))
    if candidate is None:
        return 0.0

    reward_report = score_attack_plan_candidate(
        candidate,
        task_info=normalize_task_metadata(info),
        require_task_match=require_info or info is not None,
    )
    return float(reward_report["reward"])


def load_environment(num_examples: int = -1, **kwargs: Any) -> Any:
    try:
        import verifiers as vf
        from datasets import Dataset
    except ImportError as exc:
        raise RuntimeError(
            "Prime Verifiers environment requires optional packages "
            "`verifiers` and `datasets`. Install this environment from "
            "`prime_intellect/verifiers_environment`."
        ) from exc

    async def accepted_attack_plan(
        completion: list[dict[str, Any]],
        info: dict[str, Any] | str | None = None,
        **_: Any,
    ) -> float:
        return score_attack_plan_completion(
            completion,
            info=info,
            require_info=True,
        )

    dataset = Dataset.from_list(build_dataset_rows(num_examples=num_examples))
    rubric = vf.Rubric(funcs=[accepted_attack_plan])
    return vf.SingleTurnEnv(
        dataset=dataset,
        rubric=rubric,
        system_prompt=SYSTEM_PROMPT,
        **kwargs,
    )


def _row_for_plan(path: Path) -> dict[str, Any]:
    raw_json = path.read_text(encoding="utf-8")
    plan = AttackPlan.model_validate_json(raw_json)
    info = task_metadata_for_plan(
        plan,
        source_path=str(path.relative_to(PACKAGE_DIR)),
        seed_attack_plan_json=raw_json,
    )
    question = "\n".join(
        [
            "Submit exactly one AttackPlan JSON object for the target below.",
            "Do not submit Python or any executable code.",
            "Toy/demo verifier output only; do not claim real-world PQC breaks.",
            "",
            "Seed AttackPlan:",
            raw_json,
        ]
    )
    return {
        "prompt": [{"role": "user", "content": question}],
        "answer": (
            "accepted" if info["seed_accepted"] else info["seed_evaluation_status"]
        ),
        "info": info,
    }


def _last_content(completion: list[dict[str, Any]]) -> str:
    if not completion:
        return ""
    content = completion[-1].get("content", "")
    return content if isinstance(content, str) else ""


def _single_json_object_text(text: str) -> str | None:
    stripped = text.strip()
    if not stripped.startswith("{"):
        return None

    decoder = json.JSONDecoder()
    try:
        value, end = decoder.raw_decode(stripped)
    except json.JSONDecodeError:
        return None
    if not isinstance(value, dict):
        return None
    if stripped[end:].strip():
        return None
    return stripped
