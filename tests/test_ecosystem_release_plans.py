from __future__ import annotations

import json
from pathlib import Path

PLAN_PATHS = {
    "huggingface": Path("docs/HUGGINGFACE_RELEASE_PLAN.md"),
    "prime": Path("docs/PRIME_INTELLECT_RELEASE_PLAN.md"),
    "nvidia": Path("docs/NVIDIA_AND_ACCELERATOR_STRATEGY.md"),
}

SCHEMA_ARTIFACTS = (
    "prime_intellect/schemas/attack_plan.schema.json",
    "prime_intellect/schemas/task_metadata.schema.json",
    "prime_intellect/schemas/schema_manifest.json",
    "prime_intellect/schemas/verifier_result.schema.json",
)
PRIME_ECOSYSTEM_ANCHORS = (
    "https://app.primeintellect.ai/dashboard/home/quickstart",
    "https://www.primeintellect.ai/auto-nanogpt",
    "PrimeIntellect-ai/experiments-autonomous-speedrunning",
)
PREFLIGHT_COMMANDS = (
    "agades-pqc publication-preflight --out public/publication_preflight.json",
    (
        "agades-pqc publication-preflight-verify --preflight "
        "public/publication_preflight.json"
    ),
)
PRIVATE_RUN_POLICY_COMMANDS = (
    "agades-pqc private-run-policy --out docs/private_run_policy.json",
    "agades-pqc private-run-policy-verify --policy docs/private_run_policy.json",
)
PRIME_QUICKSTART_COMMANDS = (
    "uv tool install -U prime",
    "prime login",
    "prime lab setup",
    (
        "prime eval run primeintellect/reverse-text "
        "-m openai/gpt-oss-20b -p prime -n 1 -r 1 -t 512 -s -A"
    ),
    (
        "prime eval run primeintellect/aime2026 "
        "-m openai/gpt-oss-20b -p prime -n 1 -r 1 -t 2048 -s -A"
    ),
    "prime eval run <owner>/agades-pqc-verifier-env",
)
PRIME_AUTONOMY_HARNESS_TERMS = (
    "AGENTS.md",
    "docs/PLAN.md",
    "docs/IMPLEMENT.md",
    "docs/STATUS.md",
    "public/run_export/manifest.json",
    "docs/private_run_policy.json",
    "scratchpad/THREAD.md",
    "external Prime autonomous run has not been performed",
)


def test_ecosystem_release_plans_cover_current_bundles_and_schema_contracts() -> None:
    dataset_info = json.loads(Path("hf/dataset/dataset_info.json").read_text())
    plans = {
        name: path.read_text(encoding="utf-8")
        for name, path in PLAN_PATHS.items()
    }
    combined = "\n".join(plans.values())

    for bundle_id in dataset_info["public_run_bundles"]:
        assert bundle_id in plans["huggingface"]
        assert bundle_id in plans["prime"]
        assert bundle_id in plans["nvidia"]

    for name, text in plans.items():
        for artifact_path in SCHEMA_ARTIFACTS:
            assert artifact_path in text, f"{name} missing {artifact_path}"

    for name, text in plans.items():
        for anchor in PRIME_ECOSYSTEM_ANCHORS:
            assert anchor in text, f"{name} missing {anchor}"
    for anchor in PRIME_ECOSYSTEM_ANCHORS:
        assert anchor in combined
    assert "downscaled MLWE public run bundles" not in plans["prime"]


def test_ecosystem_release_plans_preserve_public_safety_boundaries() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8") for path in PLAN_PATHS.values()
    )

    required_boundaries = (
        "No real private evolution traces",
        "not a security claim",
        "Prime Hub publication requires credentials",
        "No GPU workload is claimed in the current MVP",
    )
    for boundary in required_boundaries:
        assert boundary in combined


def test_huggingface_release_plan_documents_space_hub_workflow() -> None:
    plan = PLAN_PATHS["huggingface"].read_text(encoding="utf-8")

    assert (
        "hf repos create agades/agades-pqc-gym-agent-env --type=space"
        in plan
    )
    assert (
        "hf upload agades/agades-pqc-gym-agent-env hf . --repo-type=space"
        in plan
    )
    assert "HF_TOKEN" in plan
    assert "Use a private Space first" in plan


def test_ecosystem_release_plans_document_publication_preflight() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8") for path in PLAN_PATHS.values()
    )

    for command in PREFLIGHT_COMMANDS:
        assert command in combined
    assert "public/publication_preflight.json" in combined


def test_ecosystem_release_plans_document_private_run_policy() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8") for path in PLAN_PATHS.values()
    )

    for command in PRIVATE_RUN_POLICY_COMMANDS:
        assert command in combined
    assert "docs/private_run_policy.json" in combined


def test_prime_release_plan_documents_current_quickstart_commands() -> None:
    plan = PLAN_PATHS["prime"].read_text(encoding="utf-8")

    for command in PRIME_QUICKSTART_COMMANDS:
        assert command in plan
    assert "external Prime execution has not been performed" in plan


def test_prime_release_plan_documents_autonomy_harness_alignment() -> None:
    plan = PLAN_PATHS["prime"].read_text(encoding="utf-8")

    for term in PRIME_AUTONOMY_HARNESS_TERMS:
        assert term in plan
