from __future__ import annotations

import hashlib
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
    REWARD_TERMS,
    RL_REWARD_REPORT_SCHEMA,
    ROLLOUT_TRACE_SCHEMA,
    AgadesPQCGymEnvironment,
)
from agades_pqc_gym.verifier import verify_attack_plan_json

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
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
    summary = _verifier_summary(result)
    return summary, json.dumps(_json_safe(result), indent=2, sort_keys=True)


def load_environment_observation(label: str) -> str:
    raw_plan = load_example_plan(label)
    env = _environment_for_raw_plan(raw_plan, source_path=f"hf-space:{label}")
    observation = env.reset()
    return json.dumps(_json_safe(observation), indent=2, sort_keys=True)


def score_attack_plan_for_task(label: str, raw_plan: str) -> tuple[str, str, str]:
    task: dict[str, Any] | None = None
    try:
        task_seed = load_example_plan(label)
        task = _task_for_raw_plan(task_seed, source_path=f"hf-space:{label}")
        env = AgadesPQCGymEnvironment([task], root=SPACE_RUNTIME_ROOT)
        env.reset()
        step = env.step(raw_plan)
        reward_report = step["info"]["reward_report"]
        trace = step["info"]["trace"]
    except Exception as exc:  # noqa: BLE001 - UI boundary must not leak tracebacks.
        reason = f"runtime_error: {_safe_error_message(exc)}"
        reward_report = _minimal_reward_report(
            raw_plan,
            blocking_reason="runtime_error",
            reason=reason,
        )
        trace = _fallback_rollout_trace(task, raw_plan, reward_report)
    summary = _reward_summary(reward_report, trace)
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
        [_task_for_raw_plan(raw_plan, source_path=source_path)],
        root=SPACE_RUNTIME_ROOT,
    )


def _task_for_raw_plan(raw_plan: str, *, source_path: str) -> dict[str, Any]:
    plan = AttackPlan.model_validate_json(raw_plan)
    return task_metadata_for_plan(
        plan,
        source_path=source_path,
        seed_attack_plan_json=raw_plan,
    )


def _space_runtime_bundle_exists(path: Path) -> bool:
    required_paths = (
        path / "docs" / "formal_attackplan_semantics.json",
        path / "docs" / "formal_operator_semantics.json",
        path / "docs" / "formal_estimator_model.json",
        path / "docs" / "reviewer_governance.json",
        path / "formal" / "lean" / "AgadesPQC" / "AttackPlan.lean",
        path / "formal" / "lean" / "AgadesPQC" / "ProofObligation.lean",
    )
    return all(required.is_file() for required in required_paths)


SPACE_RUNTIME_ROOT = APP_DIR if _space_runtime_bundle_exists(APP_DIR) else ROOT


def _verifier_summary(result: dict[str, Any]) -> str:
    status = result["evaluation_status"]
    family = result["target_family"] or "unknown"
    score = result["combined_score"]
    if status == "invalid":
        reason = (
            _first_text(result.get("validation_errors"))
            or "schema validation failed"
        )
        return (
            f"Invalid AttackPlan JSON: {reason}. "
            "Toy/demo output only; not a security claim."
        )
    score = "n/a" if status == "unsupported" else result["combined_score"]
    return (
        f"{family}: {status}; score={score}. "
        "Toy/demo output only; not a security claim."
    )


def _reward_summary(
    reward_report: dict[str, Any],
    trace: dict[str, Any],
) -> str:
    formal_binding = trace.get("formal_artifact_binding", {})
    return (
        f"reward={reward_report['reward']}; "
        f"accepted={str(reward_report['accepted']).lower()}; "
        f"reason={_reward_reason(reward_report)}; "
        f"review_governance={_review_governance_status(formal_binding)}. "
        "Toy/demo Agent Environment output only; not a security claim."
    )


def _reward_reason(reward_report: dict[str, Any]) -> str:
    diagnostic = reward_report.get("diagnostic")
    if isinstance(diagnostic, dict) and isinstance(diagnostic.get("reason"), str):
        return diagnostic["reason"]
    validation_error = _first_text(reward_report.get("validation_errors"))
    verifier_summary = reward_report.get("verifier_summary")
    if isinstance(verifier_summary, dict):
        family = verifier_summary.get("target_family")
        status = verifier_summary.get("evaluation_status")
        if verifier_summary.get("schema_valid") is False and validation_error:
            return f"Invalid AttackPlan JSON: {validation_error}"
        if status == "unsupported":
            family_label = family if isinstance(family, str) else "target"
            return (
                f"{family_label} targets are schema_only or unsupported in this "
                "public Space"
            )
    blocking = reward_report.get("blocking_reasons")
    if isinstance(blocking, list) and blocking:
        return "blocked_by=" + ",".join(str(item) for item in blocking)
    if reward_report.get("accepted") is True:
        return "accepted"
    return "not_accepted"


def _minimal_reward_report(
    candidate_json: str,
    *,
    blocking_reason: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "schema_version": RL_REWARD_REPORT_SCHEMA,
        "reward": 0.0,
        "accepted": False,
        "blocked": True,
        "blocking_reasons": [blocking_reason],
        "terms": dict.fromkeys(REWARD_TERMS, 0.0),
        "pedagogical_reward": {
            "schema_version": "agades.pqc.rl.pedagogical_reward.v1",
            "base_reward": 0.0,
            "pedagogy_multiplier": 1.0,
            "final_reward": 0.0,
            "signal_error": False,
            "signals": {},
        },
        "formal_summary": {
            "accepted": False,
            "attackplan_semantics": {},
            "operator_semantics": {},
            "formal_estimator_model": {},
            "family_invariants": 0,
            "proof_obligations": 0,
            "typed_proof_obligations": 0,
            "proof_obligation_type_rules": 0,
            "type_rule_kinds": [],
            "lean_theorems": 0,
            "required_reviewers": 0,
            "claim_boundary_ok": False,
            "review_governance": {},
            "review_governance_ok": False,
        },
        "verifier_summary": {
            "schema_valid": False,
            "accepted": False,
            "evaluation_status": "runtime_error",
            "target_family": _candidate_summary(candidate_json)["target_family"],
            "safety": {
                "arbitrary_code_execution": False,
                "live_targeting": False,
                "security_claim": False,
            },
        },
        "claim_boundary": {
            "trains_agent_behavior": True,
            "claims_pqc_break": False,
            "requires_human_review_before_claim": True,
        },
        "validation_errors": [reason],
        "diagnostic": {"reason": reason},
    }


def _fallback_rollout_trace(
    task: dict[str, Any] | None,
    candidate_json: str,
    reward_report: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": ROLLOUT_TRACE_SCHEMA,
        "task": task,
        "candidate": _candidate_summary(candidate_json),
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


def _first_text(value: Any) -> str | None:
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str) and item:
                return item
    if isinstance(value, str) and value:
        return value
    return None


def _safe_error_message(exc: Exception) -> str:
    message = str(exc).strip()
    if not message:
        return exc.__class__.__name__
    return message


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _review_governance_status(formal_binding: object) -> str:
    if not isinstance(formal_binding, dict):
        return "missing"
    if formal_binding.get("review_governance_ok") is True:
        return "accepted"
    return "rejected"


if __name__ == "__main__":
    build_demo().launch()
