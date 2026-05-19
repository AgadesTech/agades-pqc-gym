from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.core.target import TargetFamily
from agades_pqc_gym.families.plugins import plugin_descriptor_entries_by_family
from agades_pqc_gym.formal.artifacts import (
    BACKEND,
    LEAN_THEOREM_SOURCES,
    MVP_VERTICAL_PROOF_ARTIFACT_PATHS,
    build_attack_plan_proof_artifact_from_json,
)
from agades_pqc_gym.formal.review import required_reviewers_for_family
from agades_pqc_gym.utils.hashing import stable_sha256

FORMAL_FAMILY_COVERAGE_SCHEMA = "agades.pqc.formal.family_coverage.v1"
FORMAL_FAMILY_COVERAGE_VERIFICATION_SCHEMA = (
    "agades.pqc.formal.family_coverage_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_COVERAGE_PATH = Path("docs/formal_family_coverage.json")
REPRESENTATIVE_ATTACK_PLANS = {
    TargetFamily.LWE: Path("examples/attack_plans/lattice_primal_usvp_toy.json"),
    TargetFamily.MLWE: Path(
        "examples/attack_plans/lattice_mlwe_module_hypothesis_toy.json"
    ),
    TargetFamily.NTRU: Path(
        "examples/attack_plans/lattice_ntru_schema_placeholder.json"
    ),
    TargetFamily.SIS: Path(
        "examples/attack_plans/lattice_sis_schema_placeholder.json"
    ),
    TargetFamily.CODE_BASED: Path(
        "examples/attack_plans/code_based_isd_placeholder.json"
    ),
    TargetFamily.MULTIVARIATE: Path("examples/attack_plans/multivariate_mq_toy.json"),
    TargetFamily.HASH_BASED: Path(
        "examples/attack_plans/hash_based_collision_toy.json"
    ),
    TargetFamily.ISOGENY_HISTORICAL: Path(
        "examples/attack_plans/isogeny_historical_toy.json"
    ),
    TargetFamily.IMPLEMENTATION_SECURITY: Path(
        "examples/attack_plans/implementation_security_kat_toy.json"
    ),
}
LINKED_ARTIFACT_PATHS = {
    "family_plugin_manifest": "docs/family_plugin_manifest.json",
    "formal_operator_semantics": "docs/formal_operator_semantics.json",
    "formal_lwe_proof_artifact": MVP_VERTICAL_PROOF_ARTIFACT_PATHS[
        TargetFamily.LWE.value
    ],
    "formal_mlwe_proof_artifact": MVP_VERTICAL_PROOF_ARTIFACT_PATHS[
        TargetFamily.MLWE.value
    ],
}


def build_formal_family_coverage(root: Path | None = None) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    plugin_entries = plugin_descriptor_entries_by_family()
    families = [
        _family_coverage_entry(
            family,
            plan_path=REPRESENTATIVE_ATTACK_PLANS[family],
            plugin_entries=plugin_entries,
            root=project_root,
        )
        for family in TargetFamily
    ]
    coverage = {
        "schema_version": FORMAL_FAMILY_COVERAGE_SCHEMA,
        "project": {
            "name": "Agades PQC Gym",
            "repository": "https://github.com/AgadesTech/agades-pqc-gym",
            "package": "agades_pqc_gym",
        },
        "backend": dict(BACKEND),
        "claim_boundary": (
            "formal family coverage proves AttackPlan applicability bindings, "
            "not PQC break claims"
        ),
        "families": families,
        "summary": _summary(families),
        "linked_artifacts": _linked_artifacts(project_root),
        "release_gates": [
            "uv run pytest tests/test_formal_family_coverage.py -q",
            "uv run agades-pqc formal-family-coverage --out "
            "docs/formal_family_coverage.json",
            "uv run agades-pqc formal-family-coverage-verify --coverage "
            "docs/formal_family_coverage.json",
            "uv run agades-pqc formal-proof-artifact-verify --artifact "
            f"{MVP_VERTICAL_PROOF_ARTIFACT_PATHS[TargetFamily.LWE.value]}",
            "uv run agades-pqc formal-proof-artifact-verify --artifact "
            f"{MVP_VERTICAL_PROOF_ARTIFACT_PATHS[TargetFamily.MLWE.value]}",
        ],
    }
    coverage["coverage_sha256"] = _coverage_sha256(coverage)
    return coverage


def write_formal_family_coverage(
    out: Path = DEFAULT_COVERAGE_PATH,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    coverage = build_formal_family_coverage(root=project_root)
    resolved = _resolve_path(out, project_root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        json.dumps(coverage, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return coverage


def verify_formal_family_coverage(
    coverage_path: Path = DEFAULT_COVERAGE_PATH,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    coverage = _read_json_object(
        _resolve_path(coverage_path, project_root),
        "Formal family coverage",
        failures,
    )
    expected = build_formal_family_coverage(root=project_root)
    if coverage and coverage != expected:
        failures.append("Formal family coverage is not in sync.")
    if coverage:
        _verify_coverage_shape(coverage, failures)
        _verify_coverage_hash(coverage, failures)
        _verify_family_entries(coverage, project_root, failures)
        _verify_linked_artifacts(coverage, expected, project_root, failures)

    summary = {
        "families": len(coverage.get("families", [])),
        "family_invariants": sum(
            len(entry.get("family_invariant_ids", []))
            for entry in _list_or_empty(coverage.get("families"))
            if isinstance(entry, dict)
        ),
        "proof_obligations": sum(
            len(entry.get("proof_obligation_ids", []))
            for entry in _list_or_empty(coverage.get("families"))
            if isinstance(entry, dict)
        ),
        "operator_semantics": sum(
            len(entry.get("operator_semantics", []))
            for entry in _list_or_empty(coverage.get("families"))
            if isinstance(entry, dict)
        ),
        "linked_artifacts": len(coverage.get("linked_artifacts", {})),
        "failure_count": len(failures),
    }
    return {
        "schema_version": FORMAL_FAMILY_COVERAGE_VERIFICATION_SCHEMA,
        "coverage_path": coverage_path.as_posix(),
        "accepted": not failures,
        "summary": summary,
        "failures": failures,
    }


def _family_coverage_entry(
    family: TargetFamily,
    *,
    plan_path: Path,
    plugin_entries: dict[TargetFamily, Any],
    root: Path,
) -> dict[str, Any]:
    raw = _resolve_path(plan_path, root).read_text(encoding="utf-8")
    artifact = build_attack_plan_proof_artifact_from_json(
        raw,
        source_label=plan_path.as_posix(),
    )
    _, descriptor, plugin_entry = plugin_entries[family]
    entry = {
        "family": family.value,
        "plugin": descriptor.name,
        "support_level": plugin_entry.support_level,
        "applicability_validator": plugin_entry.applicability_validator,
        "representative_attack_plan": {
            "path": plan_path.as_posix(),
            "attack_plan_id": artifact["attack_plan"]["id"],
            "sha256": artifact["attack_plan"]["sha256"],
            "canonical_sha256": artifact["attack_plan"]["canonical_sha256"],
        },
        "family_invariant_ids": [
            invariant["invariant_id"]
            for invariant in artifact["family_invariants"]
        ],
        "proof_obligation_ids": [
            obligation["obligation_id"]
            for obligation in artifact["proof_obligations"]
        ],
        "operator_semantics": list(artifact["operator_semantics"]),
        "lean_bindings": _lean_bindings(artifact),
        "estimator_model": dict(artifact["estimator_model"]),
        "required_reviewers": required_reviewers_for_family(family),
        "review_status": artifact["review"]["status"],
        "claim_boundary": artifact["review"]["claim_boundary"],
    }
    entry["entry_sha256"] = stable_sha256(entry)
    return entry


def _lean_bindings(artifact: dict[str, Any]) -> list[dict[str, str]]:
    observed: dict[str, dict[str, str]] = {}
    for item in [
        *artifact["family_invariants"],
        *artifact["proof_obligations"],
    ]:
        lean_theorem = item["lean_theorem"]
        source = item["lean_source"]
        observed[lean_theorem] = {
            "lean_theorem": lean_theorem,
            "path": source["path"],
            "declaration": source["declaration"],
            "sha256": source["sha256"],
        }
    return [observed[key] for key in sorted(observed)]


def _summary(families: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "families": len(families),
        "family_invariants": sum(
            len(entry["family_invariant_ids"]) for entry in families
        ),
        "proof_obligations": sum(
            len(entry["proof_obligation_ids"]) for entry in families
        ),
        "operator_semantics": sum(
            len(entry["operator_semantics"]) for entry in families
        ),
        "schema_only_families": [
            entry["family"]
            for entry in families
            if entry["support_level"] == "schema_only"
        ],
        "implemented_or_toy_families": [
            entry["family"]
            for entry in families
            if entry["support_level"] != "schema_only"
        ],
    }


def _verify_coverage_shape(
    coverage: dict[str, Any],
    failures: list[str],
) -> None:
    if coverage.get("schema_version") != FORMAL_FAMILY_COVERAGE_SCHEMA:
        failures.append(
            "Formal family coverage schema_version must be "
            f"{FORMAL_FAMILY_COVERAGE_SCHEMA}."
        )
    if coverage.get("backend") != BACKEND:
        failures.append("Formal family coverage backend must be Lean 4 + Mathlib.")
    if "not PQC break claims" not in coverage.get("claim_boundary", ""):
        failures.append("Formal family coverage must state the no-overclaim boundary.")
    families = _list_or_empty(coverage.get("families"))
    if coverage.get("summary") != _summary(
        [entry for entry in families if isinstance(entry, dict)]
    ):
        failures.append("Formal family coverage summary is inconsistent.")


def _verify_coverage_hash(
    coverage: dict[str, Any],
    failures: list[str],
) -> None:
    if coverage.get("coverage_sha256") != _coverage_sha256(coverage):
        failures.append("Formal family coverage hash does not match its payload.")


def _verify_family_entries(
    coverage: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    entries = _list_or_empty(coverage.get("families"))
    expected_families = [family.value for family in TargetFamily]
    if [
        entry.get("family") for entry in entries if isinstance(entry, dict)
    ] != expected_families:
        failures.append(
            "Formal family coverage must contain one entry for each TargetFamily."
        )
    for raw_entry in entries:
        if not isinstance(raw_entry, dict):
            failures.append("Formal family coverage entries must be objects.")
            continue
        _verify_family_entry(raw_entry, root, failures)


def _verify_family_entry(
    entry: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    family_name = entry.get("family")
    try:
        family = TargetFamily(family_name)
    except ValueError:
        failures.append(f"Formal family coverage family is unsupported: {family_name}.")
        return
    if entry.get("entry_sha256") != _entry_sha256(entry):
        failures.append(f"Formal family coverage entry hash mismatch: {family.value}.")
    if not entry.get("applicability_validator"):
        failures.append(f"Formal family coverage lacks validator: {family.value}.")
    if not entry.get("family_invariant_ids"):
        failures.append(f"Formal family coverage lacks invariants: {family.value}.")
    if not entry.get("proof_obligation_ids"):
        failures.append(f"Formal family coverage lacks obligations: {family.value}.")
    if any(
        str(invariant_id).endswith(".family_shape_validated")
        for invariant_id in _list_or_empty(entry.get("family_invariant_ids"))
    ):
        failures.append(
            "Formal family coverage must not use generic fallback invariants."
        )
    if entry.get("required_reviewers") != required_reviewers_for_family(family):
        failures.append(
            f"Formal family coverage reviewers are incorrect: {family.value}."
        )
    if entry.get("review_status") != "pending_review":
        failures.append(
            f"Formal family coverage review status is incorrect: {family.value}."
        )
    if "not PQC break claims" not in entry.get("claim_boundary", ""):
        failures.append(
            f"Formal family coverage claim boundary is missing: {family.value}."
        )
    if _dict_or_empty(entry.get("estimator_model")).get("no_fake_estimate") is not True:
        failures.append(
            f"Formal family coverage estimator boundary is incorrect: {family.value}."
        )
    _verify_plan_binding(entry, root, failures)
    _verify_lean_bindings(entry, root, failures)


def _verify_plan_binding(
    entry: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    plan = _dict_or_empty(entry.get("representative_attack_plan"))
    path_value = plan.get("path")
    if not isinstance(path_value, str) or not path_value:
        failures.append("Formal family coverage representative path is missing.")
        return
    plan_path = root / path_value
    try:
        raw = plan_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        failures.append(
            f"Formal family coverage representative plan is missing: {path_value}."
        )
        return
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        failures.append(
            f"Formal family coverage representative plan is invalid JSON: {path_value}."
        )
        return
    if plan.get("sha256") != hashlib.sha256(raw.encode("utf-8")).hexdigest():
        failures.append(
            f"Formal family coverage plan SHA mismatch: {path_value}."
        )
    if plan.get("canonical_sha256") != stable_sha256(payload):
        failures.append(
            f"Formal family coverage plan canonical SHA mismatch: {path_value}."
        )


def _verify_lean_bindings(
    entry: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    bindings = _list_or_empty(entry.get("lean_bindings"))
    if not bindings:
        failures.append(
            f"Formal family coverage lacks Lean bindings: {entry.get('family')}."
        )
        return
    for binding in bindings:
        if not isinstance(binding, dict):
            failures.append("Formal family coverage Lean binding must be an object.")
            continue
        lean_theorem = binding.get("lean_theorem")
        if not isinstance(lean_theorem, str):
            failures.append("Formal family coverage Lean theorem is missing.")
            continue
        expected_path = LEAN_THEOREM_SOURCES.get(lean_theorem)
        if binding.get("path") != expected_path:
            failures.append(
                f"Formal family coverage Lean path mismatch: {lean_theorem}."
            )
            continue
        source_path = root / expected_path
        try:
            raw = source_path.read_bytes()
        except FileNotFoundError:
            failures.append(
                f"Formal family coverage Lean source is missing: {expected_path}."
            )
            continue
        if binding.get("sha256") != hashlib.sha256(raw).hexdigest():
            failures.append(
                f"Formal family coverage Lean source hash mismatch: {expected_path}."
            )
        declaration = lean_theorem.rsplit(".", 1)[1]
        if binding.get("declaration") != declaration:
            failures.append(
                f"Formal family coverage Lean declaration mismatch: {lean_theorem}."
            )
        if f"theorem {declaration}" not in raw.decode("utf-8"):
            failures.append(
                f"Formal family coverage Lean theorem is missing: {lean_theorem}."
            )


def _verify_linked_artifacts(
    coverage: dict[str, Any],
    expected: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    linked = coverage.get("linked_artifacts")
    if not isinstance(linked, dict):
        failures.append("Formal family coverage linked_artifacts must be an object.")
        return
    if linked != expected.get("linked_artifacts"):
        failures.append(
            "Formal family coverage linked artifact hashes are not in sync."
        )
    for name, artifact in linked.items():
        if not isinstance(artifact, dict):
            failures.append(f"Formal family coverage linked artifact {name} invalid.")
            continue
        path = artifact.get("path")
        if not isinstance(path, str) or not (root / path).is_file():
            failures.append(f"Formal family coverage linked artifact missing: {name}.")
        if artifact.get("sha256") is None:
            failures.append(
                f"Formal family coverage linked artifact lacks SHA: {name}."
            )


def _coverage_sha256(coverage: dict[str, Any]) -> str:
    payload = {
        key: value for key, value in coverage.items() if key != "coverage_sha256"
    }
    return stable_sha256(payload)


def _entry_sha256(entry: dict[str, Any]) -> str:
    payload = {
        key: value for key, value in entry.items() if key != "entry_sha256"
    }
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
