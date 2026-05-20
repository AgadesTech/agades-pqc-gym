from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.core.registry import default_family_registry
from agades_pqc_gym.core.target import TargetFamily
from agades_pqc_gym.evaluators.mock_estimator import MockEstimatorAdapter
from agades_pqc_gym.families.code_based.isd_estimator import (
    ToyCodeBasedISDEstimator,
)
from agades_pqc_gym.families.hash_based.bound_estimator import ToyHashBoundEstimator
from agades_pqc_gym.families.implementation_security.kat_estimator import (
    ToyImplementationSecurityEstimator,
)
from agades_pqc_gym.families.isogeny_historical.path_estimator import (
    ToyIsogenyHistoricalPathEstimator,
)
from agades_pqc_gym.families.multivariate.mq_estimator import (
    ToyMultivariateMQEstimator,
)
from agades_pqc_gym.families.plugins import plugin_descriptor_entries_by_family
from agades_pqc_gym.formal.artifacts import (
    BACKEND,
    LEAN_THEOREM_SOURCES,
    MVP_VERTICAL_PROOF_ARTIFACT_PATHS,
)
from agades_pqc_gym.formal.review import required_reviewers_for_family
from agades_pqc_gym.utils.hashing import stable_sha256

FORMAL_ESTIMATOR_MODEL_SCHEMA = "agades.pqc.formal.estimator_model.v1"
FORMAL_ESTIMATOR_MODEL_VERIFICATION_SCHEMA = (
    "agades.pqc.formal.estimator_model_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ESTIMATOR_MODEL_PATH = Path("docs/formal_estimator_model.json")
NO_SECURITY_CLAIM_THEOREMS = [
    "AgadesPQC.Evaluator.attached_unreviewed_no_security_claim",
    "AgadesPQC.Evaluator.no_security_claim",
    "AgadesPQC.Evaluator.schema_only_no_estimator_no_security_claim",
]
LINKED_ARTIFACT_PATHS = {
    "family_plugin_manifest": "docs/family_plugin_manifest.json",
    "formal_family_coverage": "docs/formal_family_coverage.json",
    "formal_lean_backend": "docs/formal_lean_backend.json",
    "formal_lwe_proof_artifact": MVP_VERTICAL_PROOF_ARTIFACT_PATHS[
        TargetFamily.LWE.value
    ],
    "formal_mlwe_proof_artifact": MVP_VERTICAL_PROOF_ARTIFACT_PATHS[
        TargetFamily.MLWE.value
    ],
}
ESTIMATOR_MODEL_IDS = {
    TargetFamily.LWE: MockEstimatorAdapter.estimator_name,
    TargetFamily.MLWE: MockEstimatorAdapter.estimator_name,
    TargetFamily.NTRU: "schema_only_no_estimator",
    TargetFamily.SIS: "schema_only_no_estimator",
    TargetFamily.CODE_BASED: ToyCodeBasedISDEstimator.estimator_name,
    TargetFamily.MULTIVARIATE: ToyMultivariateMQEstimator.estimator_name,
    TargetFamily.HASH_BASED: ToyHashBoundEstimator.estimator_name,
    TargetFamily.ISOGENY_HISTORICAL: (
        ToyIsogenyHistoricalPathEstimator.estimator_name
    ),
    TargetFamily.IMPLEMENTATION_SECURITY: (
        ToyImplementationSecurityEstimator.estimator_name
    ),
}


def build_formal_estimator_model(root: Path | None = None) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    families = _family_models()
    model = {
        "schema_version": FORMAL_ESTIMATOR_MODEL_SCHEMA,
        "project": {
            "name": "Agades PQC Gym",
            "repository": "https://github.com/AgadesTech/agades-pqc-gym",
            "package": "agades_pqc_gym",
        },
        "backend": dict(BACKEND),
        "claim_boundary": (
            "estimator outputs are reproducibility or toy-evaluation bindings, "
            "not PQC break claims"
        ),
        "proof_artifact_binding": {
            "estimator_result_binding_required_before_claim": True,
            "accepted_public_binding_statuses": [
                "not_attached",
                "attached_unreviewed",
            ],
            "security_claim_status_without_review": "disallowed",
            "lean_theorem": "AgadesPQC.Evaluator.no_security_claim",
            "mvp_vertical_proof_artifacts": dict(MVP_VERTICAL_PROOF_ARTIFACT_PATHS),
        },
        "estimator_result_contract": {
            "required_fields": [
                "estimator_name",
                "estimator_version",
                "evaluation_status",
                "attack_type",
                "time_bits",
                "memory_bits",
                "warnings",
            ],
            "hash_binding_fields": [
                "path",
                "sha256",
                "canonical_sha256",
            ],
            "claim_allowed_before_review": False,
        },
        "lean_bindings": _lean_bindings(project_root),
        "families": families,
        "summary": _summary(families),
        "linked_artifacts": _linked_artifacts(project_root),
        "release_gates": [
            "uv run pytest tests/test_formal_estimator_model.py -q",
            "uv run agades-pqc formal-estimator-model --out "
            "docs/formal_estimator_model.json",
            "uv run agades-pqc formal-estimator-model-verify --model "
            "docs/formal_estimator_model.json",
            "uv run agades-pqc formal-family-coverage-verify --coverage "
            "docs/formal_family_coverage.json",
        ],
    }
    model["model_sha256"] = _model_sha256(model)
    return model


def write_formal_estimator_model(
    out: Path = DEFAULT_ESTIMATOR_MODEL_PATH,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    model = build_formal_estimator_model(root=project_root)
    resolved = _resolve_path(out, project_root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        json.dumps(model, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return model


def verify_formal_estimator_model(
    model_path: Path = DEFAULT_ESTIMATOR_MODEL_PATH,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    model = _read_json_object(
        _resolve_path(model_path, project_root),
        "Formal estimator model",
        failures,
    )
    expected = build_formal_estimator_model(root=project_root)
    if model and model != expected:
        failures.append("Formal estimator model is not in sync.")
    if model:
        _verify_model_shape(model, failures)
        _verify_model_hash(model, failures)
        _verify_lean_bindings(model, project_root, failures)
        _verify_family_entries(model, failures)
        _verify_linked_artifacts(model, expected, project_root, failures)

    families = [
        entry
        for entry in _list_or_empty(model.get("families"))
        if isinstance(entry, dict)
    ]
    summary = {
        "families": len(families),
        "runtime_operator_count": sum(
            int(entry.get("runtime_operator_count", 0)) for entry in families
        ),
        "linked_artifacts": len(model.get("linked_artifacts", {})),
        "failure_count": len(failures),
    }
    return {
        "schema_version": FORMAL_ESTIMATOR_MODEL_VERIFICATION_SCHEMA,
        "model_path": model_path.as_posix(),
        "accepted": not failures,
        "summary": summary,
        "failures": failures,
    }


def _family_models() -> list[dict[str, Any]]:
    registry = default_family_registry()
    plugin_entries = plugin_descriptor_entries_by_family()
    families: list[dict[str, Any]] = []
    for family in TargetFamily:
        _, descriptor, plugin_entry = plugin_entries[family]
        adapter = registry.get(family)
        supported_operators = sorted(adapter.supported_operators())
        entry = {
            "family": family.value,
            "plugin": descriptor.name,
            "adapter_class": plugin_entry.adapter_class,
            "plugin_support_level": plugin_entry.support_level,
            "adapter_support_level": adapter.support_level,
            "supported_operators": supported_operators,
            "runtime_operator_count": len(supported_operators),
            "estimator_model": _estimator_model(family, adapter.support_level),
            "claim_policy": {
                "estimator_output_is_security_proof": False,
                "security_claim_allowed_without_review": False,
                "human_review_required_before_security_claim": True,
                "proof_artifact_binding_required": True,
                "lean_theorem": "AgadesPQC.Evaluator.no_security_claim",
            },
            "required_reviewers": required_reviewers_for_family(family),
        }
        entry["entry_sha256"] = _entry_sha256(entry)
        families.append(entry)
    return families


def _estimator_model(
    family: TargetFamily,
    adapter_support_level: str,
) -> dict[str, Any]:
    if adapter_support_level == "schema_only":
        return {
            "model_id": "schema_only_no_estimator",
            "status": "schema_only_no_estimator",
            "result_binding_required_before_claim": False,
            "security_claim_allowed_without_review": False,
            "toy_or_mock_result": False,
        }
    return {
        "model_id": ESTIMATOR_MODEL_IDS[family],
        "status": "result_binding_required_before_claim",
        "result_binding_required_before_claim": True,
        "security_claim_allowed_without_review": False,
        "toy_or_mock_result": True,
    }


def _summary(families: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "families": len(families),
        "runtime_operator_count": sum(
            entry["runtime_operator_count"] for entry in families
        ),
        "result_binding_required_before_claim": sum(
            1
            for entry in families
            if entry["estimator_model"]["result_binding_required_before_claim"]
        ),
        "schema_only_no_estimator": sum(
            1
            for entry in families
            if entry["estimator_model"]["status"] == "schema_only_no_estimator"
        ),
        "security_claim_allowed_without_review": sum(
            1
            for entry in families
            if entry["claim_policy"]["security_claim_allowed_without_review"]
        ),
    }


def _lean_bindings(root: Path) -> list[dict[str, str]]:
    return [
        _lean_binding(lean_theorem, root)
        for lean_theorem in NO_SECURITY_CLAIM_THEOREMS
    ]


def _lean_binding(lean_theorem: str, root: Path) -> dict[str, str]:
    path = LEAN_THEOREM_SOURCES[lean_theorem]
    declaration = lean_theorem.rsplit(".", 1)[1]
    source_path = root / path
    return {
        "lean_theorem": lean_theorem,
        "path": path,
        "declaration": declaration,
        "sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
    }


def _verify_model_shape(model: dict[str, Any], failures: list[str]) -> None:
    if model.get("schema_version") != FORMAL_ESTIMATOR_MODEL_SCHEMA:
        failures.append(
            "Formal estimator model schema_version must be "
            f"{FORMAL_ESTIMATOR_MODEL_SCHEMA}."
        )
    if model.get("backend") != BACKEND:
        failures.append("Formal estimator model backend must be Lean 4 + Mathlib.")
    if "not PQC break claims" not in model.get("claim_boundary", ""):
        failures.append("Formal estimator model must state the no-overclaim boundary.")
    binding = _dict_or_empty(model.get("proof_artifact_binding"))
    if binding.get("security_claim_status_without_review") != "disallowed":
        failures.append(
            "Formal estimator model proof binding must disallow unreviewed claims."
        )
    if binding.get("mvp_vertical_proof_artifacts") != MVP_VERTICAL_PROOF_ARTIFACT_PATHS:
        failures.append(
            "Formal estimator model must bind both LWE and MLWE proof artifacts."
        )
    families = [
        entry
        for entry in _list_or_empty(model.get("families"))
        if isinstance(entry, dict)
    ]
    if model.get("summary") != _summary(families):
        failures.append("Formal estimator model summary is inconsistent.")


def _verify_model_hash(model: dict[str, Any], failures: list[str]) -> None:
    if model.get("model_sha256") != _model_sha256(model):
        failures.append("Formal estimator model hash does not match its payload.")


def _verify_lean_bindings(
    model: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    bindings = _list_or_empty(model.get("lean_bindings"))
    observed_theorems = [
        binding.get("lean_theorem")
        for binding in bindings
        if isinstance(binding, dict)
    ]
    if observed_theorems != NO_SECURITY_CLAIM_THEOREMS:
        failures.append("Formal estimator model Lean bindings are incomplete.")
    for binding in bindings:
        if not isinstance(binding, dict):
            failures.append("Formal estimator model Lean binding must be an object.")
            continue
        lean_theorem = binding.get("lean_theorem")
        if not isinstance(lean_theorem, str):
            failures.append("Formal estimator model Lean theorem is missing.")
            continue
        expected_path = LEAN_THEOREM_SOURCES.get(lean_theorem)
        if binding.get("path") != expected_path:
            failures.append(
                f"Formal estimator model Lean path mismatch: {lean_theorem}."
            )
            continue
        source_path = root / expected_path
        try:
            raw = source_path.read_bytes()
        except FileNotFoundError:
            failures.append(
                f"Formal estimator model Lean source is missing: {expected_path}."
            )
            continue
        declaration = lean_theorem.rsplit(".", 1)[1]
        if binding.get("sha256") != hashlib.sha256(raw).hexdigest():
            failures.append(
                f"Formal estimator model Lean source hash mismatch: {expected_path}."
            )
        if binding.get("declaration") != declaration:
            failures.append(
                f"Formal estimator model Lean declaration mismatch: {lean_theorem}."
            )
        if f"theorem {declaration}" not in raw.decode("utf-8"):
            failures.append(
                f"Formal estimator model Lean theorem is missing: {lean_theorem}."
            )


def _verify_family_entries(model: dict[str, Any], failures: list[str]) -> None:
    entries = _list_or_empty(model.get("families"))
    expected_families = [family.value for family in TargetFamily]
    if [
        entry.get("family") for entry in entries if isinstance(entry, dict)
    ] != expected_families:
        failures.append(
            "Formal estimator model must contain one entry for each TargetFamily."
        )
    for raw_entry in entries:
        if not isinstance(raw_entry, dict):
            failures.append("Formal estimator model family entry must be an object.")
            continue
        _verify_family_entry(raw_entry, failures)


def _verify_family_entry(entry: dict[str, Any], failures: list[str]) -> None:
    family_name = entry.get("family")
    try:
        family = TargetFamily(family_name)
    except ValueError:
        failures.append(f"Formal estimator model family is unsupported: {family_name}.")
        return
    if entry.get("entry_sha256") != _entry_sha256(entry):
        failures.append(f"Formal estimator model entry hash mismatch: {family.value}.")
    claim_policy = _dict_or_empty(entry.get("claim_policy"))
    estimator_model = _dict_or_empty(entry.get("estimator_model"))
    if claim_policy.get("security_claim_allowed_without_review") is not False:
        failures.append(
            "Formal estimator model must not allow unreviewed security claims."
        )
    if estimator_model.get("security_claim_allowed_without_review") is not False:
        failures.append(
            "Formal estimator model estimator states must not allow unreviewed claims."
        )
    if entry.get("required_reviewers") != required_reviewers_for_family(family):
        failures.append(
            f"Formal estimator model reviewers are incorrect: {family.value}."
        )
    if entry.get("adapter_support_level") == "schema_only":
        if estimator_model.get("model_id") != "schema_only_no_estimator":
            failures.append(
                "Formal estimator model schema-only families must not name "
                "runtime estimators."
            )
        if estimator_model.get("result_binding_required_before_claim") is not False:
            failures.append(
                "Formal estimator model schema-only families must not require "
                "runtime result bindings."
            )
    else:
        if estimator_model.get("result_binding_required_before_claim") is not True:
            failures.append(
                f"Formal estimator model must bind results before claims: "
                f"{family.value}."
            )


def _verify_linked_artifacts(
    model: dict[str, Any],
    expected: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    linked = model.get("linked_artifacts")
    if not isinstance(linked, dict):
        failures.append("Formal estimator model linked_artifacts must be an object.")
        return
    if linked != expected.get("linked_artifacts"):
        failures.append(
            "Formal estimator model linked artifact hashes are not in sync."
        )
    for name, artifact in linked.items():
        if not isinstance(artifact, dict):
            failures.append(f"Formal estimator model linked artifact {name} invalid.")
            continue
        path = artifact.get("path")
        if not isinstance(path, str) or not (root / path).is_file():
            failures.append(f"Formal estimator model linked artifact missing: {name}.")
        if artifact.get("sha256") is None:
            failures.append(
                f"Formal estimator model linked artifact lacks SHA: {name}."
            )


def _model_sha256(model: dict[str, Any]) -> str:
    payload = {key: value for key, value in model.items() if key != "model_sha256"}
    return stable_sha256(payload)


def _entry_sha256(entry: dict[str, Any]) -> str:
    payload = {key: value for key, value in entry.items() if key != "entry_sha256"}
    return stable_sha256(payload)


def _linked_artifacts(root: Path) -> dict[str, dict[str, str | None]]:
    return {
        name: {
            "path": path,
            "sha256": _file_sha256(root / path),
        }
        for name, path in LINKED_ARTIFACT_PATHS.items()
    }


def _file_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except FileNotFoundError:
        return None


def _read_json_object(
    path: Path,
    label: str,
    failures: list[str],
) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"{label} is missing: {path.as_posix()}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(f"{label} is invalid JSON at line {exc.lineno}.")
        return {}
    if not isinstance(payload, dict):
        failures.append(f"{label} must be a JSON object.")
        return {}
    return payload


def _resolve_path(path: Path, root: Path) -> Path:
    return path if path.is_absolute() else root / path


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_or_empty(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []
