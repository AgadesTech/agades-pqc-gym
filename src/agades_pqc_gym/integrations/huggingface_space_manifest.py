from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.rl.environment import (
    OBSERVATION_SCHEMA,
    RL_REWARD_REPORT_SCHEMA,
    ROLLOUT_TRACE_SCHEMA,
)
from agades_pqc_gym.verifier import PUBLIC_VERIFIER_SCHEMA

HF_SPACE_MANIFEST_SCHEMA = "agades.pqc.hf_space_manifest.v1"
HF_SPACE_MANIFEST_VERIFICATION_SCHEMA = (
    "agades.pqc.hf_space_manifest_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LABEL = "LWE / lattice_primal_usvp_toy_v1"
_EXPECTED_FALSE_SAFETY_FLAGS = (
    "contains_private_traces",
    "arbitrary_code_execution",
    "live_targeting",
    "security_claim",
    "publishes_private_candidates",
)
_REQUIRED_RELEASE_GATES = (
    "uv run pytest tests/test_huggingface_space_manifest.py -q",
    "uv run agades-pqc hf-dataset --out hf/dataset",
    "uv run agades-pqc hf-dataset-verify --dataset hf/dataset",
    "uv run agades-pqc hf-space-manifest --out hf/space_manifest.json",
    "uv run agades-pqc hf-space-manifest-verify --manifest hf/space_manifest.json",
    "uv run agades-pqc hf-space-smoke --out reports/hf_space_smoke.json",
    "uv run agades-pqc hf-space-smoke-verify --report reports/hf_space_smoke.json",
    "uv run agades-pqc ecosystem-smoke-verify --report "
    "reports/ecosystem_smoke.json",
    "uv run agades-pqc release-audit --out public/release_audit.json",
)


def build_huggingface_space_manifest(root: Path | None = None) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    example_index = _public_example_index(project_root / "hf" / "dataset")
    labels = example_index["labels"]

    default_label = DEFAULT_LABEL if DEFAULT_LABEL in labels else labels[0]
    return {
        "schema_version": HF_SPACE_MANIFEST_SCHEMA,
        "project": {
            "name": "Agades PQC Gym Space",
            "package": "agades-pqc-gym",
            "repository": "https://github.com/AgadesTech/agades-pqc-gym",
            "app_path": "hf/app.py",
        },
        "space": {
            "suggested_space_id": "AgadesTech/agades-pqc-gym-agent-env",
            "sdk": "gradio",
            "category": "agent-environment",
            "app_file": "hf/app.py",
            "requirements_file": "hf/requirements.txt",
            "dataset_bundle": "hf/dataset",
            "hub_create_command_template": (
                "hf repos create AgadesTech/agades-pqc-gym-agent-env --type=space "
                "--space-sdk gradio --private --exist-ok"
            ),
            "hub_upload_command_template": (
                "hf upload AgadesTech/agades-pqc-gym-agent-env hf "
                '. --repo-type=space --commit-message "Sync Agades PQC Gym '
                'Agent Environment"'
            ),
            "public_push_requires_review": True,
        },
        "runtime": {
            "requirements": _requirements(project_root / "hf" / "requirements.txt"),
            "dataset_source": "hf/dataset/attack_plans.jsonl",
            "task_metadata_source": "hf/dataset/task_metadata.jsonl",
            "rollout_examples_source": "hf/dataset/rl_rollouts.jsonl",
            "fallback_source": "examples/attack_plans",
            "requires_gradio_to_launch": True,
            "requires_gradio_to_import_for_audit": False,
        },
        "agent_environment_contract": {
            "environment_class": (
                "agades_pqc_gym.rl.environment.AgadesPQCGymEnvironment"
            ),
            "observation_schema": OBSERVATION_SCHEMA,
            "reward_report_schema": RL_REWARD_REPORT_SCHEMA,
            "rollout_trace_schema": ROLLOUT_TRACE_SCHEMA,
            "task_dataset": "hf/dataset/task_metadata.jsonl",
            "rollout_examples": "hf/dataset/rl_rollouts.jsonl",
            "scoring_function": (
                "agades_pqc_gym.rl.environment.score_attack_plan_candidate"
            ),
            "task_interface": "single_turn_attackplan_json",
            "public_track_only": True,
            "private_trace_publication_allowed": False,
            "claims_pqc_breaks": False,
        },
        "example_manifest": {
            "default_label": default_label,
            "dataset_attack_plan_count": example_index["dataset_attack_plan_count"],
            "dataset_valid_attack_plan_count": example_index[
                "dataset_valid_attack_plan_count"
            ],
            "dataset_invalid_attack_plan_count": example_index[
                "dataset_invalid_attack_plan_count"
            ],
            "example_count": len(labels),
            "excluded_attack_plan_ids": example_index["excluded_attack_plan_ids"],
            "families": example_index["families"],
            "labels": labels,
            "labels_match_valid_dataset_rows": example_index[
                "labels_match_valid_dataset_rows"
            ],
        },
        "verifier_contract": {
            "verifier_schema": PUBLIC_VERIFIER_SCHEMA,
            "uses_shared_verifier": True,
            "accepts_arbitrary_code": False,
            "accepts_live_targets": False,
            "output_security_claim": False,
            "summary_must_include": "not a security claim",
        },
        "safety": {
            "contains_private_traces": False,
            "arbitrary_code_execution": False,
            "live_targeting": False,
            "security_claim": False,
            "publishes_private_candidates": False,
        },
        "release": {
            "publication_status": "local_artifact_ready",
            "requires_credentials": True,
            "review_required_before_publish": True,
            "smoke_gate": "hf-space-smoke",
            "audit_gate": "hf-space-manifest",
        },
        "release_gates": list(_REQUIRED_RELEASE_GATES),
    }


def write_huggingface_space_manifest(
    out: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    manifest = build_huggingface_space_manifest(root=root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def verify_huggingface_space_manifest(
    manifest_path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    manifest = _read_huggingface_space_manifest(manifest_path, project_root, failures)
    expected = build_huggingface_space_manifest(root=project_root)

    if manifest != expected:
        failures.append("Hugging Face Space manifest is not in sync.")

    _verify_project_metadata(manifest, failures)
    _verify_space_contract(manifest, expected, failures)
    _verify_runtime(project_root, manifest, failures)
    _verify_agent_environment_contract(project_root, manifest, failures)
    _verify_example_manifest(project_root, manifest, failures)
    _verify_verifier_contract(manifest, failures)
    _verify_safety(manifest, failures)
    _verify_release_contract(manifest, failures)
    _verify_release_gates(manifest, failures)

    return _verification_result(manifest_path, manifest, failures)


def _read_huggingface_space_manifest(
    manifest_path: Path,
    root: Path,
    failures: list[str],
) -> dict[str, Any]:
    path = manifest_path if manifest_path.is_absolute() else root / manifest_path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"Hugging Face Space manifest is missing: {manifest_path}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(
            f"Hugging Face Space manifest is invalid JSON at line {exc.lineno}."
        )
        return {}

    if not isinstance(payload, dict):
        failures.append("Hugging Face Space manifest must be a JSON object.")
        return {}
    return payload


def _verify_project_metadata(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    if manifest.get("schema_version") != HF_SPACE_MANIFEST_SCHEMA:
        failures.append(
            "Hugging Face Space manifest schema_version must be "
            f"{HF_SPACE_MANIFEST_SCHEMA}."
        )
    project = manifest.get("project")
    if not isinstance(project, dict):
        failures.append("Hugging Face Space manifest project must be an object.")
        return
    expected_project = {
        "name": "Agades PQC Gym Space",
        "package": "agades-pqc-gym",
        "repository": "https://github.com/AgadesTech/agades-pqc-gym",
        "app_path": "hf/app.py",
    }
    for key, expected in expected_project.items():
        if project.get(key) != expected:
            failures.append(f"Hugging Face Space manifest project.{key} is incorrect.")


def _verify_space_contract(
    manifest: dict[str, Any],
    expected: dict[str, Any],
    failures: list[str],
) -> None:
    space = manifest.get("space")
    if not isinstance(space, dict):
        failures.append("Hugging Face Space manifest space must be an object.")
        return
    expected_space = expected.get("space", {})
    for field in (
        "suggested_space_id",
        "sdk",
        "app_file",
        "requirements_file",
        "dataset_bundle",
        "hub_create_command_template",
        "hub_upload_command_template",
    ):
        if space.get(field) != expected_space.get(field):
            failures.append(f"Hugging Face Space manifest has incorrect {field}.")
    if space.get("category") != "agent-environment":
        failures.append("Hugging Face Space manifest is not an Agent Environment.")
    if space.get("public_push_requires_review") is not True:
        failures.append("Hugging Face Space manifest lacks public push review gate.")


def _verify_runtime(
    root: Path,
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    runtime = manifest.get("runtime")
    if not isinstance(runtime, dict):
        failures.append("Hugging Face Space manifest runtime must be an object.")
        return
    if runtime.get("requirements") != _requirements(root / "hf" / "requirements.txt"):
        failures.append("Hugging Face Space manifest requirements are not in sync.")
    if runtime.get("dataset_source") != "hf/dataset/attack_plans.jsonl":
        failures.append("Hugging Face Space manifest dataset_source is incorrect.")
    if runtime.get("task_metadata_source") != "hf/dataset/task_metadata.jsonl":
        failures.append(
            "Hugging Face Space manifest task_metadata_source is incorrect."
        )
    if runtime.get("rollout_examples_source") != "hf/dataset/rl_rollouts.jsonl":
        failures.append(
            "Hugging Face Space manifest rollout_examples_source is incorrect."
        )
    for field in ("dataset_source", "task_metadata_source", "rollout_examples_source"):
        path = runtime.get(field)
        if isinstance(path, str) and not (root / path).is_file():
            failures.append(
                "Hugging Face Space manifest runtime file is missing: "
                f"{path}."
            )
    if runtime.get("fallback_source") != "examples/attack_plans":
        failures.append("Hugging Face Space manifest fallback_source is incorrect.")
    if runtime.get("requires_gradio_to_launch") is not True:
        failures.append("Hugging Face Space manifest launch boundary is incorrect.")
    if runtime.get("requires_gradio_to_import_for_audit") is not False:
        failures.append("Hugging Face Space manifest audit import boundary drifted.")


def _verify_agent_environment_contract(
    root: Path,
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    contract = manifest.get("agent_environment_contract")
    if not isinstance(contract, dict):
        failures.append(
            "Hugging Face Space manifest agent_environment_contract must be an object."
        )
        return
    expected = {
        "environment_class": "agades_pqc_gym.rl.environment.AgadesPQCGymEnvironment",
        "observation_schema": OBSERVATION_SCHEMA,
        "reward_report_schema": RL_REWARD_REPORT_SCHEMA,
        "rollout_trace_schema": ROLLOUT_TRACE_SCHEMA,
        "task_dataset": "hf/dataset/task_metadata.jsonl",
        "rollout_examples": "hf/dataset/rl_rollouts.jsonl",
        "scoring_function": "agades_pqc_gym.rl.environment.score_attack_plan_candidate",
        "task_interface": "single_turn_attackplan_json",
        "public_track_only": True,
        "private_trace_publication_allowed": False,
        "claims_pqc_breaks": False,
    }
    if contract != expected:
        failures.append("Hugging Face Space Agent Environment contract drifted.")
    for field in ("task_dataset", "rollout_examples"):
        path = contract.get(field)
        if not isinstance(path, str) or not (root / path).is_file():
            failures.append(
                f"Hugging Face Space Agent Environment file is missing: {path}."
            )
    if contract.get("public_track_only") is not True:
        failures.append(
            "Hugging Face Space Agent Environment must be public-track only."
        )
    if contract.get("private_trace_publication_allowed") is not False:
        failures.append(
            "Hugging Face Space Agent Environment must not publish private traces."
        )
    if contract.get("claims_pqc_breaks") is not False:
        failures.append(
            "Hugging Face Space Agent Environment must not claim PQC breaks."
        )
    try:
        app_module = _load_python_module(
            root / "hf" / "app.py",
            "agades_pqc_hf_space_agent_environment_verifier",
        )
        label = app_module.DEFAULT_EXAMPLE_LABEL
        raw_plan = app_module.load_example_plan(label)
        observation = json.loads(app_module.load_environment_observation(label))
        _summary, reward_report, trace = app_module.score_attack_plan_for_task(
            label,
            raw_plan,
        )
        reward = json.loads(reward_report)
        rollout = json.loads(trace)
    except Exception as exc:  # noqa: BLE001 - verifier must report app issues.
        failures.append(
            "Hugging Face Space Agent Environment app comparison failed: "
            f"{exc}"
        )
        return
    if observation.get("schema_version") != OBSERVATION_SCHEMA:
        failures.append("Hugging Face Space Agent Environment observation drifted.")
    if reward.get("schema_version") != RL_REWARD_REPORT_SCHEMA:
        failures.append("Hugging Face Space Agent Environment reward schema drifted.")
    if rollout.get("schema_version") != ROLLOUT_TRACE_SCHEMA:
        failures.append("Hugging Face Space Agent Environment trace schema drifted.")
    if rollout.get("private_fields_present") is not False:
        failures.append("Hugging Face Space Agent Environment exposes private fields.")


def _verify_example_manifest(
    root: Path,
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    examples = manifest.get("example_manifest")
    if not isinstance(examples, dict):
        failures.append(
            "Hugging Face Space manifest example_manifest must be an object."
        )
        return
    dataset_info_path = root / "hf" / "dataset" / "dataset_info.json"
    try:
        dataset_info = json.loads(dataset_info_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        dataset_info = {}
        failures.append("Hugging Face dataset info is missing.")
    except json.JSONDecodeError as exc:
        dataset_info = {}
        failures.append(f"Hugging Face dataset info is invalid JSON: {exc}.")

    if examples.get("dataset_attack_plan_count") != dataset_info.get(
        "attack_plan_count"
    ):
        failures.append(
            "Hugging Face Space manifest dataset row count differs from dataset info."
        )
    if examples.get("dataset_valid_attack_plan_count") != dataset_info.get(
        "valid_attack_plan_count"
    ):
        failures.append(
            "Hugging Face Space manifest valid row count differs from dataset info."
        )
    if examples.get("dataset_invalid_attack_plan_count") != dataset_info.get(
        "invalid_attack_plan_count"
    ):
        failures.append(
            "Hugging Face Space manifest invalid row count differs from dataset info."
        )
    if examples.get("excluded_attack_plan_ids") != dataset_info.get(
        "invalid_attack_plan_ids"
    ):
        failures.append(
            "Hugging Face Space manifest excluded ids differ from dataset info."
        )
    if examples.get("labels_match_valid_dataset_rows") is not True:
        failures.append(
            "Hugging Face Space manifest labels do not match valid dataset rows."
        )
    if examples.get("example_count") != examples.get(
        "dataset_valid_attack_plan_count"
    ):
        failures.append(
            "Hugging Face Space selector count differs from valid dataset rows."
        )
    labels = examples.get("labels")
    if not isinstance(labels, list) or not all(
        isinstance(label, str) for label in labels
    ):
        failures.append("Hugging Face Space manifest labels must be a string list.")
        labels = []
    families = examples.get("families")
    if not isinstance(families, list) or not all(
        isinstance(family, str) for family in families
    ):
        failures.append("Hugging Face Space manifest families must be a string list.")

    try:
        app_module = _load_python_module(
            root / "hf" / "app.py",
            "agades_pqc_hf_space_manifest_verifier",
        )
        app_choices = app_module.example_plan_choices()
        app_default = app_module.DEFAULT_EXAMPLE_LABEL
    except Exception as exc:  # noqa: BLE001 - verifier must report app issues.
        failures.append(f"Hugging Face Space manifest app comparison failed: {exc}")
        return
    if labels != app_choices:
        failures.append("Hugging Face Space manifest labels differ from app choices.")
    if examples.get("default_label") != app_default:
        failures.append("Hugging Face Space manifest default differs from app default.")
    if examples.get("default_label") not in labels:
        failures.append("Hugging Face Space manifest default is not selectable.")


def _verify_verifier_contract(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    verifier_contract = manifest.get("verifier_contract")
    if not isinstance(verifier_contract, dict):
        failures.append(
            "Hugging Face Space manifest verifier_contract must be an object."
        )
        return
    if verifier_contract.get("verifier_schema") != PUBLIC_VERIFIER_SCHEMA:
        failures.append("Hugging Face Space manifest verifier schema drifted.")
    if verifier_contract.get("uses_shared_verifier") is not True:
        failures.append("Hugging Face Space manifest does not use shared verifier.")
    if verifier_contract.get("accepts_arbitrary_code") is not False:
        failures.append("Hugging Face Space manifest allows arbitrary code.")
    if verifier_contract.get("accepts_live_targets") is not False:
        failures.append("Hugging Face Space manifest allows live targets.")
    if verifier_contract.get("output_security_claim") is not False:
        failures.append("Hugging Face Space manifest advertises security claims.")
    if verifier_contract.get("summary_must_include") != "not a security claim":
        failures.append("Hugging Face Space manifest summary boundary drifted.")


def _verify_safety(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    safety = manifest.get("safety")
    if not isinstance(safety, dict):
        failures.append("Hugging Face Space manifest safety must be an object.")
        return
    for flag in _EXPECTED_FALSE_SAFETY_FLAGS:
        if safety.get(flag) is not False:
            if flag == "arbitrary_code_execution":
                failures.append(
                    "Hugging Face Space manifest advertises arbitrary execution."
                )
            elif flag == "contains_private_traces":
                failures.append(
                    "Hugging Face Space manifest may expose private traces."
                )
            elif flag == "security_claim":
                failures.append(
                    "Hugging Face Space manifest advertises a security claim."
                )
            elif flag == "publishes_private_candidates":
                failures.append(
                    "Hugging Face Space manifest may publish private candidates."
                )
            else:
                failures.append(
                    f"Hugging Face Space manifest safety.{flag} must be false."
                )


def _verify_release_contract(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    release = manifest.get("release")
    if not isinstance(release, dict):
        failures.append("Hugging Face Space manifest release must be an object.")
        return
    if release.get("publication_status") != "local_artifact_ready":
        failures.append("Hugging Face Space manifest publication status is incorrect.")
    if release.get("requires_credentials") is not True:
        failures.append("Hugging Face Space manifest lacks credential boundary.")
    if release.get("review_required_before_publish") is not True:
        failures.append("Hugging Face Space manifest lacks publication review gate.")
    if release.get("smoke_gate") != "hf-space-smoke":
        failures.append("Hugging Face Space manifest does not point to smoke gate.")
    if release.get("audit_gate") != "hf-space-manifest":
        failures.append("Hugging Face Space manifest does not point to audit gate.")


def _verify_release_gates(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    release_gates = manifest.get("release_gates")
    if not isinstance(release_gates, list):
        failures.append("Hugging Face Space manifest release_gates must be a list.")
        return
    for required_gate in _REQUIRED_RELEASE_GATES:
        if required_gate not in release_gates:
            failures.append(
                f"Hugging Face Space manifest release gate missing: {required_gate}"
            )


def _verification_result(
    manifest_path: Path,
    manifest: dict[str, Any],
    failures: list[str],
) -> dict[str, Any]:
    examples = manifest.get("example_manifest", {})
    if not isinstance(examples, dict):
        examples = {}
    space = manifest.get("space", {})
    if not isinstance(space, dict):
        space = {}
    runtime = manifest.get("runtime", {})
    if not isinstance(runtime, dict):
        runtime = {}
    verifier_contract = manifest.get("verifier_contract", {})
    if not isinstance(verifier_contract, dict):
        verifier_contract = {}
    agent_environment = manifest.get("agent_environment_contract", {})
    if not isinstance(agent_environment, dict):
        agent_environment = {}
    return {
        "schema_version": HF_SPACE_MANIFEST_VERIFICATION_SCHEMA,
        "manifest_path": manifest_path.as_posix(),
        "accepted": not failures,
        "summary": {
            "dataset_attack_plan_count": examples.get("dataset_attack_plan_count"),
            "dataset_invalid_attack_plan_count": examples.get(
                "dataset_invalid_attack_plan_count"
            ),
            "dataset_valid_attack_plan_count": examples.get(
                "dataset_valid_attack_plan_count"
            ),
            "default_label": examples.get("default_label"),
            "example_count": examples.get("example_count"),
            "failure_count": len(failures),
            "is_agent_environment": (
                space.get("category") == "agent-environment"
                and agent_environment.get("observation_schema") == OBSERVATION_SCHEMA
            ),
            "labels_match_valid_dataset_rows": examples.get(
                "labels_match_valid_dataset_rows"
            ),
            "public_push_requires_review": space.get("public_push_requires_review"),
            "requires_gradio_to_import_for_audit": runtime.get(
                "requires_gradio_to_import_for_audit"
            ),
            "uses_shared_verifier": verifier_contract.get("uses_shared_verifier"),
        },
        "failures": failures,
    }


def _load_python_module(path: Path, module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _public_example_index(dataset_dir: Path) -> dict[str, Any]:
    attack_plans = dataset_dir / "attack_plans.jsonl"
    labels: list[str] = []
    families: set[str] = set()
    excluded_attack_plan_ids: list[str] = []
    dataset_attack_plan_count = 0
    dataset_valid_attack_plan_count = 0
    for line in attack_plans.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        dataset_attack_plan_count += 1
        row = json.loads(line)
        attack_plan_id = row.get("attack_plan_id", row.get("example_id", "unknown"))
        try:
            plan = AttackPlan.model_validate(row["attack_plan"])
        except (KeyError, ValidationError):
            excluded_attack_plan_ids.append(str(attack_plan_id))
            continue
        dataset_valid_attack_plan_count += 1
        if not plan.metadata.public:
            excluded_attack_plan_ids.append(plan.attack_plan_id)
            continue
        family = plan.target.family.value
        labels.append(f"{family} / {plan.attack_plan_id}")
        families.add(family)
    if not labels:
        raise ValueError("Hugging Face Space manifest requires public examples.")
    return {
        "dataset_attack_plan_count": dataset_attack_plan_count,
        "dataset_valid_attack_plan_count": dataset_valid_attack_plan_count,
        "dataset_invalid_attack_plan_count": (
            dataset_attack_plan_count - dataset_valid_attack_plan_count
        ),
        "excluded_attack_plan_ids": excluded_attack_plan_ids,
        "families": sorted(families),
        "labels": labels,
        "labels_match_valid_dataset_rows": len(labels)
        == dataset_valid_attack_plan_count,
    }


def _requirements(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
