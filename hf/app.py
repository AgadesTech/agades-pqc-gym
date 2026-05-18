from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import gradio as gr
except ImportError:  # pragma: no cover - exercised in deployments with Gradio.
    gr = None

from agades_pqc_gym.core.attack_plan import AttackPlan
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
    status = result["evaluation_status"]
    family = result["target_family"] or "unknown"
    score = result["combined_score"]
    summary = (
        f"{family}: {status}; score={score}. "
        "Toy/demo output only; not a security claim."
    )
    return summary, json.dumps(_json_safe(result), indent=2, sort_keys=True)


def build_demo() -> Any:
    if gr is None:
        raise RuntimeError("gradio is required to launch the Hugging Face Space")
    with gr.Blocks(title="Agades PQC Gym") as demo:
        gr.Markdown("# Agades PQC Gym")
        gr.Markdown(
            "Safe toy AttackPlan verifier. Outputs are estimator plumbing signals, "
            "not claims about deployed PQC standards."
        )
        selected_plan = gr.Dropdown(
            choices=example_plan_choices(),
            value=DEFAULT_EXAMPLE_LABEL,
            label="Public example",
        )
        plan = gr.Code(value=DEFAULT_PLAN, language="json", label="AttackPlan JSON")
        run = gr.Button("Evaluate")
        summary = gr.Textbox(label="Summary")
        payload = gr.Code(language="json", label="Verifier JSON")
        selected_plan.change(load_example_plan, inputs=selected_plan, outputs=plan)
        run.click(evaluate_attack_plan_json, inputs=plan, outputs=[summary, payload])
    return demo


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


if __name__ == "__main__":
    build_demo().launch()
