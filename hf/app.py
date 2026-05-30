from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
from typing import Any

try:
    import gradio as gr
except ImportError:  # pragma: no cover - exercised in deployments with Gradio.
    gr = None

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.integrations.task_metadata import task_metadata_for_plan
from agades_pqc_gym.rl.environment import (
    AgadesPQCGymEnvironment,
    score_attack_plan_candidate,
)
from agades_pqc_gym.verifier import verify_attack_plan_json

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
FORMAL_ROOT = APP_DIR if (APP_DIR / "formal" / "lean").is_dir() else ROOT
DATASET_ATTACK_PLANS = APP_DIR / "dataset" / "attack_plans.jsonl"
REPO_ATTACK_PLAN_DIR = ROOT / "examples" / "attack_plans"


def _load_example_plan_texts() -> dict[str, str]:
    if DATASET_ATTACK_PLANS.is_file():
        return _load_examples_from_dataset(DATASET_ATTACK_PLANS)
    return _load_examples_from_repo(REPO_ATTACK_PLAN_DIR)


def _load_examples_from_dataset(path: Path) -> dict[str, str]:
    examples: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        raw_plan = json.dumps(row["attack_plan"], indent=2, sort_keys=True) + "\n"
        _add_public_valid_example(examples, raw_plan)
    return examples


def _load_examples_from_repo(path: Path) -> dict[str, str]:
    examples: dict[str, str] = {}
    for plan_path in sorted(path.glob("*.json")):
        _add_public_valid_example(
            examples,
            plan_path.read_text(encoding="utf-8"),
        )
    return examples


def _add_public_valid_example(examples: dict[str, str], raw_plan: str) -> None:
    try:
        plan = AttackPlan.model_validate_json(raw_plan)
    except ValueError:
        return
    if not plan.metadata.public:
        return
    label = f"{plan.target.family.value} / {plan.attack_plan_id}"
    examples[label] = raw_plan


EXAMPLE_PLAN_TEXTS = _load_example_plan_texts()
if not EXAMPLE_PLAN_TEXTS:
    raise RuntimeError("Hugging Face Space requires at least one public AttackPlan")
DEFAULT_EXAMPLE_LABEL = (
    "LWE / lattice_primal_usvp_toy_v1"
    if "LWE / lattice_primal_usvp_toy_v1" in EXAMPLE_PLAN_TEXTS
    else next(iter(EXAMPLE_PLAN_TEXTS))
)
DEFAULT_PLAN = EXAMPLE_PLAN_TEXTS[DEFAULT_EXAMPLE_LABEL]


def example_plan_choices() -> list[str]:
    return list(EXAMPLE_PLAN_TEXTS)


def load_example_plan(label: str) -> str:
    try:
        raw_plan = EXAMPLE_PLAN_TEXTS[label]
    except KeyError as exc:
        raise ValueError(f"unknown example plan: {label}") from exc
    return raw_plan


def evaluate_attack_plan_json(raw_plan: str) -> tuple[str, str]:
    result = verify_attack_plan_json(raw_plan)
    status = result["evaluation_status"]
    family = result["target_family"] or "unknown"
    score = result["combined_score"]
    reason = _verifier_reason(result)
    reason_text = f" reason={reason}." if reason else ""
    summary = f"{family}: {status}; score={score}.{reason_text} "
    summary += "Toy/demo output only; not a security claim."
    return summary, json.dumps(_json_safe(result), indent=2, sort_keys=True)


def load_environment_observation(label: str) -> str:
    raw_plan = load_example_plan(label)
    env = _environment_for_raw_plan(raw_plan, source_path=f"hf-space:{label}")
    observation = env.reset()
    return json.dumps(_json_safe(observation), indent=2, sort_keys=True)


def score_attack_plan_for_task(label: str, raw_plan: str) -> tuple[str, str, str]:
    task_seed = load_example_plan(label)
    task = _task_for_raw_plan(task_seed, source_path=f"hf-space:{label}")
    env = AgadesPQCGymEnvironment([task])
    env.reset()
    try:
        step = env.step(raw_plan)
        reward_report = step["info"]["reward_report"]
        trace = step["info"]["trace"]
    except Exception:  # noqa: BLE001 - Space handlers must not leak raw tracebacks.
        reward_report = _score_candidate_for_space(raw_plan, task=task)
        trace = _fallback_rollout_trace(
            task=task,
            candidate_json=raw_plan,
            reward_report=reward_report,
        )
    blocked_reasons = reward_report.get("blocking_reasons") or []
    blocked_text = (
        f"blocked={','.join(str(reason) for reason in blocked_reasons)}; "
        if blocked_reasons
        else ""
    )
    reason = _reward_reason(reward_report)
    reason_text = f"reason={reason}. " if reason else ""
    summary = (
        f"reward={reward_report['reward']}; "
        f"accepted={str(reward_report['accepted']).lower()}. "
        f"{blocked_text}{reason_text}"
        "Toy/demo Agent Environment output only; not a security claim."
    )
    return (
        summary,
        json.dumps(_json_safe(reward_report), indent=2, sort_keys=True),
        json.dumps(_json_safe(trace), indent=2, sort_keys=True),
    )


def build_demo() -> Any:
    if gr is None:
        raise RuntimeError("gradio is required to launch the Hugging Face Space")
    with gr.Blocks(title="Agades PQC Gym") as demo:
        gr.Markdown("# Agades PQC Gym")
        gr.Markdown(
            "Safe toy AttackPlan verifier. Outputs are estimator plumbing signals, "
            "not claims about deployed PQC standards."
        )
        with gr.Tabs():
            with gr.Tab("Verifier"):
                selected_plan = gr.Dropdown(
                    choices=example_plan_choices(),
                    value=DEFAULT_EXAMPLE_LABEL,
                    label="Public example",
                )
                plan = gr.Code(
                    value=DEFAULT_PLAN,
                    language="json",
                    label="AttackPlan JSON",
                )
                run = gr.Button("Evaluate")
                summary = gr.Textbox(label="Summary")
                payload = gr.Code(language="json", label="Verifier JSON")
                selected_plan.change(
                    load_example_plan,
                    inputs=selected_plan,
                    outputs=plan,
                )
                run.click(
                    evaluate_attack_plan_json,
                    inputs=plan,
                    outputs=[summary, payload],
                )
            with gr.Tab("Agent Environment"):
                env_task = gr.Dropdown(
                    choices=example_plan_choices(),
                    value=DEFAULT_EXAMPLE_LABEL,
                    label="Task",
                )
                candidate = gr.Code(
                    value=DEFAULT_PLAN,
                    language="json",
                    label="Candidate AttackPlan JSON",
                )
                observe = gr.Button("Load Observation")
                score = gr.Button("Score Candidate")
                observation = gr.Code(language="json", label="Observation JSON")
                reward_summary = gr.Textbox(label="Reward Summary")
                reward_payload = gr.Code(language="json", label="Reward Report JSON")
                trace_payload = gr.Code(language="json", label="Rollout Trace JSON")
                env_task.change(load_example_plan, inputs=env_task, outputs=candidate)
                observe.click(
                    load_environment_observation,
                    inputs=env_task,
                    outputs=observation,
                )
                score.click(
                    score_attack_plan_for_task,
                    inputs=[env_task, candidate],
                    outputs=[reward_summary, reward_payload, trace_payload],
                )
    return demo


def _environment_for_raw_plan(
    raw_plan: str,
    *,
    source_path: str,
) -> AgadesPQCGymEnvironment:
    return AgadesPQCGymEnvironment(
        [_task_for_raw_plan(raw_plan, source_path=source_path)]
    )


def _task_for_raw_plan(raw_plan: str, *, source_path: str) -> dict[str, Any]:
    plan = AttackPlan.model_validate_json(raw_plan)
    return task_metadata_for_plan(
        plan,
        source_path=source_path,
        seed_attack_plan_json=raw_plan,
    )


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _verifier_reason(result: dict[str, Any]) -> str | None:
    validation_errors = result.get("validation_errors")
    if isinstance(validation_errors, list):
        for error in validation_errors:
            if isinstance(error, str) and error.strip():
                return error.strip()
    warnings = result.get("warnings")
    if isinstance(warnings, list):
        for warning in warnings:
            if isinstance(warning, str) and warning.strip():
                return warning.strip()
    return None


def _reward_reason(reward_report: dict[str, Any]) -> str | None:
    validation_errors = reward_report.get("validation_errors")
    if isinstance(validation_errors, list):
        for error in validation_errors:
            if isinstance(error, str) and error.strip():
                return error.strip()
    blocking_reasons = reward_report.get("blocking_reasons")
    if isinstance(blocking_reasons, list):
        for reason in blocking_reasons:
            if isinstance(reason, str) and reason.strip():
                return reason.strip()
    return None


def _score_candidate_for_space(
    candidate_json: str,
    *,
    task: dict[str, Any],
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "task_info": task,
        "require_task_match": True,
    }
    if "root" in inspect.signature(score_attack_plan_candidate).parameters:
        kwargs["root"] = FORMAL_ROOT
    try:
        return score_attack_plan_candidate(candidate_json, **kwargs)
    except Exception:  # noqa: BLE001 - return a public-safe non-claim fallback.
        return _minimal_reward_report(candidate_json, task=task)


def _minimal_reward_report(
    candidate_json: str,
    *,
    task: dict[str, Any],
) -> dict[str, Any]:
    verifier_result = verify_attack_plan_json(candidate_json)
    validation_errors = verifier_result.get("validation_errors")
    if not isinstance(validation_errors, list):
        validation_errors = []
    blocking_reasons = ["schema_valid", "cryptographic_applicability"]
    if task:
        blocking_reasons.append("task_match")
    return {
        "schema_version": "agades.pqc.rl.reward_report.v1",
        "reward": 0.0,
        "accepted": False,
        "blocked": True,
        "blocking_reasons": blocking_reasons,
        "terms": {
            "formal_validity": 0.0,
            "cryptographic_applicability": 0.0,
            "no_security_overclaim": 0.0,
            "student_readability": 0.0,
            "reproducibility": 0.0,
            "reviewer_quality": 0.0,
            "task_match": 0.0,
            "proof_obligation_coverage": 0.0,
        },
        "pedagogical_reward": {
            "schema_version": "agades.pqc.rl.pedagogical_reward.v1",
            "base_reward": 0.0,
            "final_reward": 0.0,
            "signal_error": False,
            "terms": {},
        },
        "formal_summary": {
            "accepted": False,
            "family_invariants": 0,
            "proof_obligations": 0,
            "typed_proof_obligations": 0,
            "proof_obligation_type_rules": 0,
            "type_rule_kinds": [],
            "lean_theorems": 0,
            "required_reviewers": 0,
            "claim_boundary_ok": False,
        },
        "verifier_summary": {
            "schema_valid": verifier_result.get("schema_valid"),
            "accepted": verifier_result.get("accepted"),
            "evaluation_status": verifier_result.get("evaluation_status"),
            "target_family": verifier_result.get("target_family"),
            "safety": verifier_result.get("safety"),
        },
        "claim_boundary": {
            "trains_agent_behavior": True,
            "claims_pqc_break": False,
            "requires_human_review_before_claim": True,
        },
        "validation_errors": validation_errors,
    }


def _fallback_rollout_trace(
    *,
    task: dict[str, Any],
    candidate_json: str,
    reward_report: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "agades.pqc.rl.rollout_trace.v1",
        "task": task,
        "candidate": _candidate_summary(candidate_json),
        "formal_artifact_binding": {
            "schema_version": "agades.pqc.rl.formal_artifact_binding.v1",
            "status": "unavailable",
            "attack_plan_id": None,
            "family": None,
            "artifact_sha256": None,
            "family_invariant_ids": [],
            "proof_obligation_ids": [],
            "proof_obligation_sha256": [],
            "proof_obligation_type_rule_sha256": [],
            "review_status": None,
            "required_reviewers": [],
            "claim_allowed": False,
            "claim_boundary": (
                "formal artifact unavailable for invalid candidate; no claim "
                "is allowed"
            ),
            "error_code": "formal_artifact_unavailable",
        },
        "reward_report": reward_report,
        "public_release_ok": True,
        "private_fields_present": False,
        "claim_boundary": {
            "claims_pqc_break": False,
            "human_review_required_before_claim": True,
        },
    }


def _candidate_summary(candidate_json: str) -> dict[str, Any]:
    sha256 = hashlib.sha256(candidate_json.encode("utf-8")).hexdigest()
    try:
        plan = AttackPlan.model_validate_json(candidate_json)
    except ValueError:
        return {
            "attack_plan_id": None,
            "target_family": None,
            "sha256": sha256,
        }
    return {
        "attack_plan_id": plan.attack_plan_id,
        "target_family": plan.target.family.value,
        "sha256": sha256,
    }


if __name__ == "__main__":
    build_demo().launch()
