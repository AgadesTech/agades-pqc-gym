from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.integrations.task_metadata import (
    TASK_METADATA_SCHEMA,
    summarize_task_metadata_rows,
    task_metadata_for_plan,
)
from agades_pqc_gym.rl.environment import (
    DEFAULT_ROLLOUT_PLANS,
    build_public_rollout_examples,
)
from agades_pqc_gym.verifier import verify_attack_plan_json

HF_DATASET_SCHEMA = "agades.pqc.hf_dataset.v1"
HF_DATASET_VERIFICATION_SCHEMA = "agades.pqc.hf_dataset_verification.v1"
HF_DATASET_NAME = "agades/pqc-gym-toy"
ATTACK_PLANS_FILENAME = "attack_plans.jsonl"
TASK_METADATA_FILENAME = "task_metadata.jsonl"
VERIFIER_OUTPUTS_FILENAME = "verifier_outputs.jsonl"
RL_ROLLOUTS_FILENAME = "rl_rollouts.jsonl"
DATASET_INFO_FILENAME = "dataset_info.json"
README_FILENAME = "README.md"
MANIFEST_FILENAME = "MANIFEST.sha256"
_REQUIRED_RELEASE_GATES = (
    "uv run pytest tests/test_huggingface_dataset_bundle.py -q",
    "uv run agades-pqc hf-dataset --out hf/dataset",
    "uv run agades-pqc hf-dataset-verify --dataset hf/dataset",
    "uv run agades-pqc hf-space-manifest-verify --manifest hf/space_manifest.json",
    "uv run agades-pqc hf-collection-manifest-verify --manifest "
    "hf/collection_manifest.json",
    "uv run agades-pqc ecosystem-smoke-verify --report "
    "reports/ecosystem_smoke.json",
    "uv run agades-pqc release-audit --out public/release_audit.json",
)
_EXPECTED_FALSE_SAFETY_FLAGS = (
    "contains_private_traces",
    "arbitrary_code_execution",
    "live_targeting",
    "security_claim",
)


def write_huggingface_dataset_bundle(
    out_dir: Path,
    *,
    root: Path | None = None,
) -> dict[str, Path]:
    project_root = _find_project_root(root)
    attack_plan_dir = project_root / "examples" / "attack_plans"
    public_run_dirs = _public_run_dirs(project_root)
    dataset_card = project_root / "hf" / "dataset_card.md"

    out_dir.mkdir(parents=True, exist_ok=True)
    public_runs_out = out_dir / "public_runs"
    if public_runs_out.exists():
        shutil.rmtree(public_runs_out)

    attack_plan_rows, verifier_rows = _build_rows(
        root=project_root,
        attack_plan_dir=attack_plan_dir,
    )

    readme_path = out_dir / README_FILENAME
    dataset_info_path = out_dir / DATASET_INFO_FILENAME
    attack_plans_path = out_dir / ATTACK_PLANS_FILENAME
    task_metadata_path = out_dir / TASK_METADATA_FILENAME
    verifier_outputs_path = out_dir / VERIFIER_OUTPUTS_FILENAME
    rl_rollouts_path = out_dir / RL_ROLLOUTS_FILENAME
    manifest_path = out_dir / MANIFEST_FILENAME
    task_metadata_rows = _task_metadata_rows(attack_plan_rows)
    rl_rollout_rows = build_public_rollout_examples(
        DEFAULT_ROLLOUT_PLANS,
        root=project_root,
    )

    readme_path.write_text(dataset_card.read_text(encoding="utf-8"), encoding="utf-8")
    dataset_info_path.write_text(
        json.dumps(
            _dataset_info(
                attack_plan_rows=attack_plan_rows,
                verifier_output_count=len(verifier_rows),
                rl_rollout_count=len(rl_rollout_rows),
                public_run_bundle_names=[path.name for path in public_run_dirs],
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    attack_plans_path.write_text(_jsonl(attack_plan_rows), encoding="utf-8")
    task_metadata_path.write_text(_jsonl(task_metadata_rows), encoding="utf-8")
    verifier_outputs_path.write_text(_jsonl(verifier_rows), encoding="utf-8")
    rl_rollouts_path.write_text(_jsonl(rl_rollout_rows), encoding="utf-8")
    for public_run_dir in public_run_dirs:
        _copy_public_run_bundle(public_run_dir, public_runs_out / public_run_dir.name)
    manifest_path.write_text(_manifest(out_dir), encoding="utf-8")

    return {
        "out_dir": out_dir,
        "readme": readme_path,
        "dataset_info": dataset_info_path,
        "attack_plans": attack_plans_path,
        "task_metadata": task_metadata_path,
        "verifier_outputs": verifier_outputs_path,
        "rl_rollouts": rl_rollouts_path,
        "manifest": manifest_path,
    }


def _build_rows(
    *,
    root: Path,
    attack_plan_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    attack_plan_rows: list[dict[str, Any]] = []
    verifier_rows: list[dict[str, Any]] = []
    for path in sorted(attack_plan_dir.glob("*.json")):
        raw_json = path.read_text(encoding="utf-8")
        relative_path = path.relative_to(root).as_posix()
        attack_plan_rows.append(_attack_plan_row(path, raw_json, relative_path))
        verifier_rows.append(_verifier_row(path, raw_json, relative_path))
    return attack_plan_rows, verifier_rows


def _attack_plan_row(path: Path, raw_json: str, relative_path: str) -> dict[str, Any]:
    data = json.loads(raw_json)
    try:
        plan = AttackPlan.model_validate_json(raw_json)
    except ValidationError:
        attack_plan_id = data.get("attack_plan_id", path.stem)
        target = data.get("target", {})
        target_family = target.get("family")
        target_name = target.get("name")
        support_level = target.get("support_level")
        task_metadata = None
        operator_types = [
            operator["type"]
            for operator in data.get("operators", [])
            if isinstance(operator, dict) and isinstance(operator.get("type"), str)
        ]
    else:
        attack_plan_id = plan.attack_plan_id
        target_family = plan.target.family.value
        target_name = plan.target.name
        support_level = plan.target.support_level.value
        task_metadata = task_metadata_for_plan(
            plan,
            source_path=relative_path,
            seed_attack_plan_json=raw_json,
        )
        operator_types = [operator.type for operator in plan.operators]

    return {
        "schema_version": HF_DATASET_SCHEMA,
        "example_id": path.stem,
        "source_path": relative_path,
        "attack_plan_id": attack_plan_id,
        "target_family": target_family,
        "target_name": target_name,
        "support_level": support_level,
        "operator_types": operator_types,
        "task_metadata": task_metadata,
        "public_example": data.get("metadata", {}).get("public") is True,
        "raw_json_sha256": hashlib.sha256(raw_json.encode("utf-8")).hexdigest(),
        "attack_plan": data,
    }


def _verifier_row(path: Path, raw_json: str, relative_path: str) -> dict[str, Any]:
    result = verify_attack_plan_json(raw_json)
    source_data = json.loads(raw_json)
    source_target = source_data.get("target", {})
    return {
        "schema_version": HF_DATASET_SCHEMA,
        "example_id": path.stem,
        "source_path": relative_path,
        "attack_plan_id": result["attack_plan_id"] or source_data.get("attack_plan_id"),
        "target_family": result["target_family"] or source_target.get("family"),
        "evaluation_status": result["evaluation_status"],
        "accepted": result["accepted"],
        "combined_score": result["combined_score"],
        "safety": result["safety"],
        "verifier_result": result,
    }


def _dataset_info(
    *,
    attack_plan_rows: list[dict[str, Any]],
    verifier_output_count: int,
    public_run_bundle_names: list[str],
    rl_rollout_count: int,
) -> dict[str, Any]:
    task_metadata_rows = _task_metadata_rows(attack_plan_rows)
    task_metadata_count = sum(
        1 for row in attack_plan_rows if row["task_metadata"] is not None
    )
    prime_task_eligible_count = sum(
        1
        for row in attack_plan_rows
        if row["task_metadata"] is not None and row["public_example"] is True
    )
    invalid_attack_plan_ids = [
        row["attack_plan_id"]
        for row in attack_plan_rows
        if row["task_metadata"] is None
    ]
    attack_plan_count = len(attack_plan_rows)
    invalid_attack_plan_count = len(invalid_attack_plan_ids)
    valid_attack_plan_count = attack_plan_count - invalid_attack_plan_count
    public_run_files = [
        f"public_runs/{bundle_name}/{filename}"
        for bundle_name in public_run_bundle_names
        for filename in (
            "README.md",
            "run_ledger.json",
            "trace_public.jsonl",
            "MANIFEST.sha256",
        )
    ]
    return {
        "schema_version": HF_DATASET_SCHEMA,
        "dataset_name": HF_DATASET_NAME,
        "task_metadata_schema": TASK_METADATA_SCHEMA,
        "attack_plan_count": attack_plan_count,
        "valid_attack_plan_count": valid_attack_plan_count,
        "invalid_attack_plan_count": invalid_attack_plan_count,
        "task_metadata_count": task_metadata_count,
        "prime_task_eligible_count": prime_task_eligible_count,
        "task_metadata_summary": summarize_task_metadata_rows(task_metadata_rows),
        "invalid_attack_plan_ids": invalid_attack_plan_ids,
        "verifier_output_count": verifier_output_count,
        "rl_rollout_count": rl_rollout_count,
        "public_run_bundles": public_run_bundle_names,
        "files": [
            README_FILENAME,
            DATASET_INFO_FILENAME,
            ATTACK_PLANS_FILENAME,
            TASK_METADATA_FILENAME,
            VERIFIER_OUTPUTS_FILENAME,
            RL_ROLLOUTS_FILENAME,
            *public_run_files,
            MANIFEST_FILENAME,
        ],
        "safety": {
            "contains_private_traces": False,
            "arbitrary_code_execution": False,
            "live_targeting": False,
            "security_claim": False,
        },
        "release_gates": [
            *_REQUIRED_RELEASE_GATES,
        ],
    }


def _task_metadata_rows(attack_plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row["task_metadata"]
        for row in attack_plan_rows
        if row["task_metadata"] is not None and row["public_example"] is True
    ]


def _public_run_dirs(root: Path) -> list[Path]:
    public_runs_root = root / "examples" / "public_runs"
    if not public_runs_root.is_dir():
        raise FileNotFoundError(
            "Hugging Face dataset export requires `examples/public_runs`."
        )
    run_dirs = sorted(path for path in public_runs_root.iterdir() if path.is_dir())
    if not run_dirs:
        raise FileNotFoundError(
            "Hugging Face dataset export requires at least one public run bundle "
            "under `examples/public_runs`."
        )
    return run_dirs


def _copy_public_run_bundle(public_run_dir: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted(public_run_dir.iterdir()):
        if path.is_file():
            shutil.copy2(path, out_dir / path.name)


def _jsonl(rows: list[dict[str, Any]]) -> str:
    return "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n"


def _manifest(root: Path) -> str:
    manifest_path = root / MANIFEST_FILENAME
    paths = sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path != manifest_path
    )
    lines = []
    for path in paths:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(root).as_posix()}")
    return "\n".join(lines) + "\n"


def verify_huggingface_dataset_bundle(
    dataset_dir: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = _find_project_root(root)
    resolved_dataset_dir = (
        dataset_dir if dataset_dir.is_absolute() else project_root / dataset_dir
    )
    failures: list[str] = []
    if not resolved_dataset_dir.is_dir():
        failures.append("Hugging Face dataset directory is missing.")

    expected = _expected_dataset_bundle(project_root)
    readme = _read_text_file(resolved_dataset_dir / README_FILENAME, failures)
    info = _read_json_file(
        resolved_dataset_dir / DATASET_INFO_FILENAME,
        "Hugging Face dataset info",
        failures,
    )
    attack_plan_rows = _read_jsonl_file(
        resolved_dataset_dir / ATTACK_PLANS_FILENAME,
        "Hugging Face dataset attack_plans.jsonl",
        failures,
    )
    task_metadata_rows = _read_jsonl_file(
        resolved_dataset_dir / TASK_METADATA_FILENAME,
        "Hugging Face dataset task_metadata.jsonl",
        failures,
    )
    verifier_rows = _read_jsonl_file(
        resolved_dataset_dir / VERIFIER_OUTPUTS_FILENAME,
        "Hugging Face dataset verifier_outputs.jsonl",
        failures,
    )
    rl_rollout_rows = _read_jsonl_file(
        resolved_dataset_dir / RL_ROLLOUTS_FILENAME,
        "Hugging Face dataset rl_rollouts.jsonl",
        failures,
    )
    manifest = _read_text_file(resolved_dataset_dir / MANIFEST_FILENAME, failures)

    _verify_file_sync(
        README_FILENAME,
        readme,
        expected["readme"],
        failures,
    )
    _verify_json_sync(
        DATASET_INFO_FILENAME,
        info,
        expected["info"],
        failures,
    )
    _verify_jsonl_sync(
        ATTACK_PLANS_FILENAME,
        attack_plan_rows,
        expected["attack_plan_rows"],
        failures,
    )
    _verify_jsonl_sync(
        TASK_METADATA_FILENAME,
        task_metadata_rows,
        expected["task_metadata_rows"],
        failures,
    )
    _verify_jsonl_sync(
        VERIFIER_OUTPUTS_FILENAME,
        verifier_rows,
        expected["verifier_rows"],
        failures,
    )
    _verify_jsonl_sync(
        RL_ROLLOUTS_FILENAME,
        rl_rollout_rows,
        expected["rl_rollout_rows"],
        failures,
    )
    _verify_public_run_mirror(
        project_root,
        resolved_dataset_dir,
        expected["public_run_bundles"],
        failures,
    )
    if manifest is not None and resolved_dataset_dir.is_dir():
        expected_manifest = _manifest(resolved_dataset_dir)
        if manifest != expected_manifest:
            failures.append("Hugging Face dataset MANIFEST.sha256 is not in sync.")

    _verify_dataset_info(info, failures)
    _verify_dataset_rows(
        info,
        attack_plan_rows,
        task_metadata_rows,
        verifier_rows,
        rl_rollout_rows,
        failures,
    )
    _verify_release_gates(info, failures)

    return _verification_result(
        dataset_dir,
        info,
        attack_plan_rows,
        task_metadata_rows,
        verifier_rows,
        rl_rollout_rows,
        manifest,
        failures,
    )


def _expected_dataset_bundle(root: Path) -> dict[str, Any]:
    attack_plan_rows, verifier_rows = _build_rows(
        root=root,
        attack_plan_dir=root / "examples" / "attack_plans",
    )
    public_run_bundles = [path.name for path in _public_run_dirs(root)]
    task_metadata_rows = _task_metadata_rows(attack_plan_rows)
    rl_rollout_rows = build_public_rollout_examples(
        DEFAULT_ROLLOUT_PLANS,
        root=root,
    )
    return {
        "readme": (root / "hf" / "dataset_card.md").read_text(encoding="utf-8"),
        "info": _dataset_info(
            attack_plan_rows=attack_plan_rows,
            verifier_output_count=len(verifier_rows),
            rl_rollout_count=len(rl_rollout_rows),
            public_run_bundle_names=public_run_bundles,
        ),
        "attack_plan_rows": attack_plan_rows,
        "task_metadata_rows": task_metadata_rows,
        "verifier_rows": verifier_rows,
        "rl_rollout_rows": rl_rollout_rows,
        "public_run_bundles": public_run_bundles,
    }


def _read_text_file(path: Path, failures: list[str]) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        failures.append(f"Hugging Face dataset file is missing: {path.name}.")
        return None


def _read_json_file(
    path: Path,
    label: str,
    failures: list[str],
) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"{label} is missing.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(f"{label} is invalid JSON at line {exc.lineno}.")
        return {}
    if not isinstance(payload, dict):
        failures.append(f"{label} must be a JSON object.")
        return {}
    return payload


def _read_jsonl_file(
    path: Path,
    label: str,
    failures: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        failures.append(f"{label} is missing.")
        return rows
    for index, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            failures.append(f"{label} has invalid JSON at line {index}: {exc.msg}.")
            continue
        if not isinstance(row, dict):
            failures.append(f"{label} line {index} must be a JSON object.")
            continue
        rows.append(row)
    return rows


def _verify_file_sync(
    filename: str,
    observed: str | None,
    expected: str,
    failures: list[str],
) -> None:
    if observed is not None and observed != expected:
        failures.append(f"Hugging Face dataset {filename} is not in sync.")


def _verify_json_sync(
    filename: str,
    observed: dict[str, Any],
    expected: dict[str, Any],
    failures: list[str],
) -> None:
    if observed and observed != expected:
        if filename == DATASET_INFO_FILENAME:
            failures.append("Hugging Face dataset info is not in sync.")
        else:
            failures.append(f"Hugging Face dataset {filename} is not in sync.")


def _verify_jsonl_sync(
    filename: str,
    observed: list[dict[str, Any]],
    expected: list[dict[str, Any]],
    failures: list[str],
) -> None:
    if observed != expected:
        failures.append(f"Hugging Face dataset {filename} is not in sync.")


def _verify_public_run_mirror(
    root: Path,
    dataset_dir: Path,
    public_run_bundles: list[str],
    failures: list[str],
) -> None:
    for bundle in public_run_bundles:
        source_dir = root / "examples" / "public_runs" / bundle
        mirrored_dir = dataset_dir / "public_runs" / bundle
        if not mirrored_dir.is_dir():
            failures.append(f"Hugging Face dataset public run is missing: {bundle}.")
            continue
        source_files = sorted(
            path.name for path in source_dir.iterdir() if path.is_file()
        )
        mirrored_files = sorted(
            path.name for path in mirrored_dir.iterdir() if path.is_file()
        )
        if mirrored_files != source_files:
            failures.append(
                f"Hugging Face dataset public run file set drifted: {bundle}."
            )
            continue
        for filename in source_files:
            if (mirrored_dir / filename).read_bytes() != (
                source_dir / filename
            ).read_bytes():
                failures.append(
                    "Hugging Face dataset public run file is not in sync: "
                    f"{bundle}/{filename}."
                )


def _verify_dataset_info(info: dict[str, Any], failures: list[str]) -> None:
    if not info:
        return
    if info.get("schema_version") != HF_DATASET_SCHEMA:
        failures.append(
            f"Hugging Face dataset schema_version must be {HF_DATASET_SCHEMA}."
        )
    if info.get("dataset_name") != HF_DATASET_NAME:
        failures.append("Hugging Face dataset name drifted.")
    if info.get("task_metadata_schema") != TASK_METADATA_SCHEMA:
        failures.append("Hugging Face dataset task metadata schema drifted.")
    safety = info.get("safety")
    if not isinstance(safety, dict):
        failures.append("Hugging Face dataset safety must be an object.")
        return
    for flag in _EXPECTED_FALSE_SAFETY_FLAGS:
        if safety.get(flag) is not False:
            if flag == "contains_private_traces":
                failures.append("Hugging Face dataset may contain private traces.")
            elif flag == "arbitrary_code_execution":
                failures.append(
                    "Hugging Face dataset advertises arbitrary execution."
                )
            elif flag == "security_claim":
                failures.append("Hugging Face dataset advertises a security claim.")
            else:
                failures.append(f"Hugging Face dataset safety.{flag} must be false.")


def _verify_dataset_rows(
    info: dict[str, Any],
    attack_plan_rows: list[dict[str, Any]],
    task_metadata_rows: list[dict[str, Any]],
    verifier_rows: list[dict[str, Any]],
    rl_rollout_rows: list[dict[str, Any]],
    failures: list[str],
) -> None:
    expected_task_metadata_rows = [
        row.get("task_metadata")
        for row in attack_plan_rows
        if row.get("task_metadata") is not None and row.get("public_example") is True
    ]
    if len(attack_plan_rows) != info.get("attack_plan_count"):
        failures.append("AttackPlan JSONL row count differs from metadata.")
    if len(task_metadata_rows) != info.get("task_metadata_count"):
        failures.append("Task metadata JSONL row count differs from metadata.")
    if len(task_metadata_rows) != info.get("prime_task_eligible_count"):
        failures.append("Task metadata JSONL row count differs from Prime count.")
    if task_metadata_rows != expected_task_metadata_rows:
        failures.append(
            "Task metadata JSONL differs from embedded AttackPlan task metadata."
        )
    try:
        task_metadata_summary = summarize_task_metadata_rows(task_metadata_rows)
    except ValueError:
        failures.append("Task metadata JSONL contains invalid task metadata.")
    else:
        if info.get("task_metadata_summary") != task_metadata_summary:
            failures.append(
                "Hugging Face dataset task metadata summary is not in sync."
            )
    if any(
        row.get("schema_version") != info.get("task_metadata_schema")
        for row in task_metadata_rows
    ):
        failures.append("Task metadata JSONL contains an unexpected schema.")
    _verify_task_metadata_seed_digests(
        attack_plan_rows,
        task_metadata_rows,
        failures,
    )
    if info.get("attack_plan_count") != info.get("verifier_output_count"):
        failures.append("AttackPlan and verifier output counts differ.")
    if len(verifier_rows) != info.get("verifier_output_count"):
        failures.append("Verifier output JSONL row count differs from metadata.")
    if any(
        row.get("safety", {}).get("security_claim") is not False
        for row in verifier_rows
    ):
        failures.append("At least one verifier row advertises a security claim.")
    if len(rl_rollout_rows) != info.get("rl_rollout_count"):
        failures.append("RL rollout JSONL row count differs from metadata.")
    if any(row.get("public_release_ok") is not True for row in rl_rollout_rows):
        failures.append("At least one RL rollout is not public-release safe.")
    if any(row.get("private_fields_present") is not False for row in rl_rollout_rows):
        failures.append("At least one RL rollout may contain private fields.")


def _verify_task_metadata_seed_digests(
    attack_plan_rows: list[dict[str, Any]],
    task_metadata_rows: list[dict[str, Any]],
    failures: list[str],
) -> None:
    expected_by_id: dict[str, str] = {}
    for row in attack_plan_rows:
        attack_plan_id = row.get("attack_plan_id")
        task_metadata = row.get("task_metadata")
        raw_json_sha256 = row.get("raw_json_sha256")
        if task_metadata is None:
            continue
        if not isinstance(attack_plan_id, str):
            failures.append("AttackPlan row with task metadata has no attack_plan_id.")
            continue
        if not isinstance(raw_json_sha256, str):
            failures.append(
                f"AttackPlan row is missing raw_json_sha256: {attack_plan_id}"
            )
            continue
        expected_by_id[attack_plan_id] = raw_json_sha256
        if not isinstance(task_metadata, dict):
            failures.append(
                f"AttackPlan row task metadata is invalid: {attack_plan_id}"
            )
            continue
        if task_metadata.get("seed_attack_plan_sha256") != raw_json_sha256:
            failures.append(
                "Task metadata seed digest does not match AttackPlan row: "
                f"{attack_plan_id}"
            )

    for row in task_metadata_rows:
        attack_plan_id = row.get("attack_plan_id")
        if not isinstance(attack_plan_id, str):
            continue
        expected_digest = expected_by_id.get(attack_plan_id)
        if expected_digest is None:
            continue
        if row.get("seed_attack_plan_sha256") != expected_digest:
            failures.append(
                "Task metadata JSONL seed digest does not match AttackPlan row: "
                f"{attack_plan_id}"
            )


def _verify_release_gates(info: dict[str, Any], failures: list[str]) -> None:
    release_gates = info.get("release_gates")
    if not isinstance(release_gates, list):
        failures.append("Hugging Face dataset release_gates must be a list.")
        return
    for required_gate in _REQUIRED_RELEASE_GATES:
        if required_gate not in release_gates:
            failures.append(
                f"Hugging Face dataset release gate missing: {required_gate}"
            )


def _verification_result(
    dataset_dir: Path,
    info: dict[str, Any],
    attack_plan_rows: list[dict[str, Any]],
    task_metadata_rows: list[dict[str, Any]],
    verifier_rows: list[dict[str, Any]],
    rl_rollout_rows: list[dict[str, Any]],
    manifest: str | None,
    failures: list[str],
) -> dict[str, Any]:
    safety = info.get("safety", {})
    if not isinstance(safety, dict):
        safety = {}
    release_gates = info.get("release_gates", [])
    if not isinstance(release_gates, list):
        release_gates = []
    manifest_entry_count = (
        len([line for line in manifest.splitlines() if line.strip()])
        if manifest is not None
        else 0
    )
    expected_task_metadata_rows = [
        row.get("task_metadata")
        for row in attack_plan_rows
        if row.get("task_metadata") is not None and row.get("public_example") is True
    ]
    task_metadata_rows_match_attack_plans = (
        task_metadata_rows == expected_task_metadata_rows
    )

    return {
        "schema_version": HF_DATASET_VERIFICATION_SCHEMA,
        "dataset_dir": dataset_dir.as_posix(),
        "accepted": not failures,
        "summary": {
            "attack_plan_count": info.get("attack_plan_count"),
            "contains_private_traces": safety.get("contains_private_traces"),
            "failure_count": len(failures),
            "invalid_attack_plan_count": info.get("invalid_attack_plan_count"),
            "invalid_attack_plan_ids": info.get("invalid_attack_plan_ids"),
            "manifest_entry_count": manifest_entry_count,
            "prime_task_eligible_count": info.get("prime_task_eligible_count"),
            "public_run_bundle_count": len(info.get("public_run_bundles", []))
            if isinstance(info.get("public_run_bundles"), list)
            else 0,
            "release_gate_count": len(release_gates),
            "security_claim": safety.get("security_claim"),
            "task_metadata_rows": len(task_metadata_rows),
            "task_metadata_rows_match_attack_plans": (
                task_metadata_rows_match_attack_plans
            ),
            "valid_attack_plan_count": info.get("valid_attack_plan_count"),
            "verifier_rows": len(verifier_rows),
            "rl_rollout_rows": len(rl_rollout_rows),
        },
        "failures": failures,
    }


def _find_project_root(root: Path | None) -> Path:
    candidates = [root] if root is not None else [Path.cwd(), *Path(__file__).parents]
    for candidate in candidates:
        if candidate is None:
            continue
        resolved = candidate.resolve()
        if (
            (resolved / "examples" / "attack_plans").is_dir()
            and (resolved / "hf" / "dataset_card.md").is_file()
        ):
            return resolved
    raise FileNotFoundError(
        "Hugging Face dataset export requires an Agades PQC Gym source checkout "
        "with `examples/attack_plans` and `hf/dataset_card.md`."
    )
