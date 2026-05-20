from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.core.target import TargetFamily
from agades_pqc_gym.formal.artifacts import (
    BACKEND,
    MVP_VERTICAL_ESTIMATOR_RESULT_PATHS,
    MVP_VERTICAL_PROOF_ARTIFACT_PATHS,
    PROOF_OBLIGATION_CLAIM_POLICY,
    build_attack_plan_proof_artifact,
    proof_obligation_type_rules,
)
from agades_pqc_gym.formal.estimator_model import DEFAULT_ESTIMATOR_MODEL_PATH
from agades_pqc_gym.formal.family_coverage import (
    DEFAULT_COVERAGE_PATH,
    REPRESENTATIVE_ATTACK_PLANS,
)
from agades_pqc_gym.formal.lean_backend import DEFAULT_BACKEND_PATH
from agades_pqc_gym.formal.operator_semantics import (
    DEFAULT_OPERATOR_SEMANTICS_PATH,
)
from agades_pqc_gym.utils.hashing import stable_sha256

FORMAL_OBLIGATION_LEDGER_SCHEMA = "agades.pqc.formal.obligation_ledger.v1"
FORMAL_OBLIGATION_LEDGER_VERIFICATION_SCHEMA = (
    "agades.pqc.formal.obligation_ledger_verification.v1"
)
DEFAULT_OBLIGATION_LEDGER_PATH = Path("docs/formal_obligation_ledger.json")
ROOT = Path(__file__).resolve().parents[3]
CLAIM_BOUNDARY = (
    "formal obligation ledger records typed applicability, invariant, "
    "estimator-boundary, and reviewer obligations; it is not a PQC break claim"
)
LINKED_ARTIFACT_PATHS = {
    "formal_family_coverage": DEFAULT_COVERAGE_PATH.as_posix(),
    "formal_operator_semantics": DEFAULT_OPERATOR_SEMANTICS_PATH.as_posix(),
    "formal_estimator_model": DEFAULT_ESTIMATOR_MODEL_PATH.as_posix(),
    "formal_lean_backend": DEFAULT_BACKEND_PATH.as_posix(),
    "formal_lwe_proof_artifact": MVP_VERTICAL_PROOF_ARTIFACT_PATHS[
        TargetFamily.LWE.value
    ],
    "formal_mlwe_proof_artifact": MVP_VERTICAL_PROOF_ARTIFACT_PATHS[
        TargetFamily.MLWE.value
    ],
    "formal_lwe_evaluator_result": MVP_VERTICAL_ESTIMATOR_RESULT_PATHS[
        TargetFamily.LWE.value
    ],
    "formal_mlwe_evaluator_result": MVP_VERTICAL_ESTIMATOR_RESULT_PATHS[
        TargetFamily.MLWE.value
    ],
}


def build_formal_obligation_ledger(root: Path | None = None) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    family_entries = [
        _family_entry(family, root=project_root) for family in TargetFamily
    ]
    proof_obligations = [
        obligation
        for family_entry in family_entries
        for obligation in family_entry["proof_obligations"]
    ]
    family_invariants = [
        invariant
        for family_entry in family_entries
        for invariant in family_entry["family_invariants"]
    ]
    ledger = {
        "schema_version": FORMAL_OBLIGATION_LEDGER_SCHEMA,
        "project": {
            "name": "Agades PQC Gym",
            "repository": "https://github.com/AgadesTech/agades-pqc-gym",
            "package": "agades_pqc_gym",
        },
        "backend": dict(BACKEND),
        "claim_boundary": CLAIM_BOUNDARY,
        "families": family_entries,
        "proof_obligation_type_rules": proof_obligation_type_rules(),
        "proof_obligations": proof_obligations,
        "family_invariants": family_invariants,
        "summary": _summary(
            family_entries,
            proof_obligations=proof_obligations,
            family_invariants=family_invariants,
        ),
        "linked_artifacts": _linked_artifacts(project_root),
        "release_gates": [
            "uv run pytest tests/test_formal_obligation_ledger.py -q",
            "uv run agades-pqc formal-obligation-ledger --out "
            "docs/formal_obligation_ledger.json",
            "uv run agades-pqc formal-obligation-ledger-verify --ledger "
            "docs/formal_obligation_ledger.json",
            "uv run agades-pqc formal-family-coverage-verify --coverage "
            "docs/formal_family_coverage.json",
            "uv run agades-pqc formal-estimator-model-verify --model "
            "docs/formal_estimator_model.json",
            "uv run agades-pqc formal-operator-semantics-verify --semantics "
            "docs/formal_operator_semantics.json",
        ],
    }
    ledger["ledger_sha256"] = _ledger_sha256(ledger)
    return ledger


def write_formal_obligation_ledger(
    out: Path = DEFAULT_OBLIGATION_LEDGER_PATH,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    ledger = build_formal_obligation_ledger(root=project_root)
    resolved = _resolve_path(out, project_root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        json.dumps(ledger, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return ledger


def verify_formal_obligation_ledger(
    ledger_path: Path = DEFAULT_OBLIGATION_LEDGER_PATH,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    resolved = _resolve_path(ledger_path, project_root)
    ledger = _read_json_object(resolved, "Formal obligation ledger", failures)
    expected = build_formal_obligation_ledger(root=project_root)
    if ledger and ledger != expected:
        failures.append("Formal obligation ledger is not in sync.")
    if ledger:
        _verify_ledger_shape(ledger, failures)
        _verify_ledger_hash(ledger, failures)
        _verify_family_entries(ledger, failures)
        _verify_obligation_entries(ledger, project_root, failures)
        _verify_invariant_entries(ledger, project_root, failures)
        _verify_linked_artifacts(ledger, expected, project_root, failures)

    families = [
        entry
        for entry in _list_or_empty(ledger.get("families"))
        if isinstance(entry, dict)
    ]
    obligations = [
        entry
        for entry in _list_or_empty(ledger.get("proof_obligations"))
        if isinstance(entry, dict)
    ]
    invariants = [
        entry
        for entry in _list_or_empty(ledger.get("family_invariants"))
        if isinstance(entry, dict)
    ]
    return {
        "schema_version": FORMAL_OBLIGATION_LEDGER_VERIFICATION_SCHEMA,
        "ledger_path": ledger_path.as_posix(),
        "accepted": not failures,
        "summary": {
            "families": len(families),
            "family_invariants": len(invariants),
            "proof_obligations": len(obligations),
            "linked_artifacts": len(ledger.get("linked_artifacts", {})),
            "failure_count": len(failures),
        },
        "failures": failures,
    }


def _family_entry(family: TargetFamily, *, root: Path) -> dict[str, Any]:
    plan_path = REPRESENTATIVE_ATTACK_PLANS[family]
    estimator_result_path = _mvp_estimator_result_path(family)
    artifact = build_attack_plan_proof_artifact(
        plan_path,
        estimator_result_path=estimator_result_path,
        root=root,
    )
    entry = {
        "family": family.value,
        "representative_attack_plan": dict(artifact["attack_plan"]),
        "representative_proof_artifact": {
            "schema_version": artifact["schema_version"],
            "artifact_sha256": artifact["artifact_sha256"],
            "estimator_result_binding_status": artifact[
                "estimator_result_binding"
            ]["status"],
            "review_status": artifact["review"]["status"],
            "required_reviewers": artifact["review"]["required_reviewers"],
        },
        "operator_semantics": list(artifact["operator_semantics"]),
        "estimator_model": dict(artifact["estimator_model"]),
        "proof_obligations": [
            _ledger_obligation_entry(family, artifact, obligation)
            for obligation in artifact["proof_obligations"]
        ],
        "family_invariants": [
            _ledger_invariant_entry(family, artifact, invariant)
            for invariant in artifact["family_invariants"]
        ],
        "required_reviewers": artifact["review"]["required_reviewers"],
        "claim_boundary": artifact["review"]["claim_boundary"],
    }
    entry["entry_sha256"] = stable_sha256(entry)
    return entry


def _ledger_obligation_entry(
    family: TargetFamily,
    artifact: dict[str, Any],
    obligation: dict[str, Any],
) -> dict[str, Any]:
    attack_plan = artifact["attack_plan"]
    entry = {
        "ledger_entry_id": f"{family.value}:{obligation['obligation_id']}",
        "family": family.value,
        "attack_plan_id": attack_plan["id"],
        "attack_plan_path": attack_plan["path"],
        "attack_plan_canonical_sha256": attack_plan["canonical_sha256"],
        "representative_proof_artifact_sha256": artifact["artifact_sha256"],
        "obligation_id": obligation["obligation_id"],
        "obligation_type": obligation["obligation_type"],
        "type_rule": obligation["type_rule"],
        "statement": obligation["statement"],
        "backend": obligation["backend"],
        "lean_theorem": obligation["lean_theorem"],
        "lean_source": obligation["lean_source"],
        "obligation_sha256": obligation["obligation_sha256"],
        "status": obligation["status"],
        "review_required": True,
        "required_reviewers": artifact["review"]["required_reviewers"],
    }
    entry["ledger_entry_sha256"] = stable_sha256(entry)
    return entry


def _ledger_invariant_entry(
    family: TargetFamily,
    artifact: dict[str, Any],
    invariant: dict[str, Any],
) -> dict[str, Any]:
    attack_plan = artifact["attack_plan"]
    entry = {
        "ledger_entry_id": f"{family.value}:{invariant['invariant_id']}",
        "family": family.value,
        "attack_plan_id": attack_plan["id"],
        "attack_plan_path": attack_plan["path"],
        "attack_plan_canonical_sha256": attack_plan["canonical_sha256"],
        "representative_proof_artifact_sha256": artifact["artifact_sha256"],
        "invariant_id": invariant["invariant_id"],
        "statement": invariant["statement"],
        "backend": "lean4",
        "lean_theorem": invariant["lean_theorem"],
        "lean_source": invariant["lean_source"],
        "review_required": True,
        "required_reviewers": artifact["review"]["required_reviewers"],
        "claim_policy": dict(PROOF_OBLIGATION_CLAIM_POLICY),
    }
    entry["ledger_entry_sha256"] = stable_sha256(entry)
    return entry


def _mvp_estimator_result_path(family: TargetFamily) -> Path | None:
    path = MVP_VERTICAL_ESTIMATOR_RESULT_PATHS.get(family.value)
    return Path(path) if path is not None else None


def _summary(
    family_entries: list[dict[str, Any]],
    *,
    proof_obligations: list[dict[str, Any]],
    family_invariants: list[dict[str, Any]],
) -> dict[str, Any]:
    lean_theorems = {
        entry["lean_theorem"]
        for entry in [
            *proof_obligations,
            *family_invariants,
            *proof_obligation_type_rules(),
        ]
    }
    reviewer_roles = {
        reviewer
        for family_entry in family_entries
        for reviewer in family_entry["required_reviewers"]
    }
    return {
        "families": len(family_entries),
        "family_invariants": len(family_invariants),
        "proof_obligations": len(proof_obligations),
        "proof_obligation_type_rules": len(proof_obligation_type_rules()),
        "lean_theorems": len(lean_theorems),
        "reviewer_roles": len(reviewer_roles),
        "attached_evaluator_result_families": [
            entry["family"]
            for entry in family_entries
            if entry["representative_proof_artifact"][
                "estimator_result_binding_status"
            ]
            == "attached_unreviewed"
        ],
        "security_claim_allowed": False,
    }


def _linked_artifacts(root: Path) -> dict[str, dict[str, Any]]:
    return {
        artifact_id: _linked_artifact(Path(path), root=root)
        for artifact_id, path in LINKED_ARTIFACT_PATHS.items()
    }


def _linked_artifact(path: Path, *, root: Path) -> dict[str, Any]:
    resolved = _resolve_path(path, root)
    raw = resolved.read_bytes()
    entry: dict[str, Any] = {
        "path": path.as_posix(),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    try:
        payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        entry["canonical_sha256"] = None
        entry["schema_version"] = None
    else:
        entry["canonical_sha256"] = stable_sha256(payload)
        entry["schema_version"] = (
            payload.get("schema_version") if isinstance(payload, dict) else None
        )
    return entry


def _verify_ledger_shape(
    ledger: dict[str, Any],
    failures: list[str],
) -> None:
    if ledger.get("schema_version") != FORMAL_OBLIGATION_LEDGER_SCHEMA:
        failures.append(
            "Formal obligation ledger schema_version must be "
            f"{FORMAL_OBLIGATION_LEDGER_SCHEMA}."
        )
    if ledger.get("backend") != BACKEND:
        failures.append("Formal obligation ledger backend must be Lean 4 + Mathlib.")
    if ledger.get("claim_boundary") != CLAIM_BOUNDARY:
        failures.append("Formal obligation ledger claim boundary is incorrect.")
    families = [
        entry
        for entry in _list_or_empty(ledger.get("families"))
        if isinstance(entry, dict)
    ]
    proof_obligations = [
        entry
        for entry in _list_or_empty(ledger.get("proof_obligations"))
        if isinstance(entry, dict)
    ]
    family_invariants = [
        entry
        for entry in _list_or_empty(ledger.get("family_invariants"))
        if isinstance(entry, dict)
    ]
    if ledger.get("summary") != _summary(
        families,
        proof_obligations=proof_obligations,
        family_invariants=family_invariants,
    ):
        failures.append("Formal obligation ledger summary is inconsistent.")
    if ledger.get("proof_obligation_type_rules") != proof_obligation_type_rules():
        failures.append("Formal obligation ledger type rules are not in sync.")


def _verify_ledger_hash(
    ledger: dict[str, Any],
    failures: list[str],
) -> None:
    if ledger.get("ledger_sha256") != _ledger_sha256(ledger):
        failures.append("Formal obligation ledger hash does not match its payload.")


def _verify_family_entries(
    ledger: dict[str, Any],
    failures: list[str],
) -> None:
    families = _list_or_empty(ledger.get("families"))
    if [
        entry.get("family") for entry in families if isinstance(entry, dict)
    ] != [family.value for family in TargetFamily]:
        failures.append("Formal obligation ledger must contain every TargetFamily.")
    for entry in families:
        if not isinstance(entry, dict):
            failures.append("Formal obligation ledger family entry must be an object.")
            continue
        payload = {key: value for key, value in entry.items() if key != "entry_sha256"}
        if entry.get("entry_sha256") != stable_sha256(payload):
            failures.append(
                f"Formal obligation ledger family hash mismatch: {entry.get('family')}."
            )
        proof_artifact = entry.get("representative_proof_artifact", {})
        if not isinstance(proof_artifact, dict):
            failures.append("Representative proof artifact binding must be an object.")
        elif proof_artifact.get("review_status") != "pending_review":
            failures.append(
                "Representative proof artifacts must remain pending review."
            )
        if "not PQC break claims" not in entry.get("claim_boundary", ""):
            failures.append("Family ledger entry must keep the no-overclaim boundary.")


def _verify_obligation_entries(
    ledger: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    obligations = _list_or_empty(ledger.get("proof_obligations"))
    expected_type_rules = {
        rule["kind"]: rule for rule in proof_obligation_type_rules()
    }
    seen: set[str] = set()
    for entry in obligations:
        if not isinstance(entry, dict):
            failures.append("Formal obligation ledger proof obligation must be object.")
            continue
        entry_id = entry.get("ledger_entry_id")
        if not isinstance(entry_id, str) or not entry_id:
            failures.append("Formal obligation ledger proof obligation lacks ID.")
        elif entry_id in seen:
            failures.append(f"Duplicate formal obligation ledger entry: {entry_id}.")
        else:
            seen.add(entry_id)
        payload = {
            key: value
            for key, value in entry.items()
            if key != "ledger_entry_sha256"
        }
        if entry.get("ledger_entry_sha256") != stable_sha256(payload):
            failures.append(
                "Formal obligation ledger entry hash mismatch: "
                f"{entry.get('ledger_entry_id')}."
            )
        obligation_type = entry.get("obligation_type")
        if not isinstance(obligation_type, dict):
            failures.append(
                f"Formal obligation type is missing: {entry.get('ledger_entry_id')}."
            )
            continue
        if obligation_type.get("claim_policy") != PROOF_OBLIGATION_CLAIM_POLICY:
            failures.append(
                "Formal obligation ledger claim policy drifted: "
                f"{entry.get('ledger_entry_id')}."
            )
        type_rule = entry.get("type_rule")
        if not isinstance(type_rule, dict):
            failures.append(
                "Formal obligation type rule is missing: "
                f"{entry.get('ledger_entry_id')}."
            )
        else:
            kind = obligation_type.get("kind")
            if type_rule.get("kind") != kind:
                failures.append(
                    "Formal obligation type rule kind mismatch: "
                    f"{entry.get('ledger_entry_id')}."
                )
            if type_rule != expected_type_rules.get(kind):
                failures.append(
                    "Formal obligation type rule drifted: "
                    f"{entry.get('ledger_entry_id')}."
                )
            _verify_nested_lean_source(
                type_rule,
                root,
                failures,
                label=f"obligation type rule {entry.get('ledger_entry_id')}",
            )
        if entry.get("status") != "pending_review":
            failures.append(
                "Formal obligation ledger entries must remain pending review."
            )
        if entry.get("backend") != "lean4":
            failures.append("Formal obligation ledger entries must target Lean 4.")
        _verify_lean_source(entry, root, failures)


def _verify_invariant_entries(
    ledger: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    invariants = _list_or_empty(ledger.get("family_invariants"))
    seen: set[str] = set()
    for entry in invariants:
        if not isinstance(entry, dict):
            failures.append("Formal obligation ledger invariant must be an object.")
            continue
        entry_id = entry.get("ledger_entry_id")
        if not isinstance(entry_id, str) or not entry_id:
            failures.append("Formal obligation ledger invariant lacks ID.")
        elif entry_id in seen:
            failures.append(f"Duplicate formal invariant ledger entry: {entry_id}.")
        else:
            seen.add(entry_id)
        payload = {
            key: value
            for key, value in entry.items()
            if key != "ledger_entry_sha256"
        }
        if entry.get("ledger_entry_sha256") != stable_sha256(payload):
            failures.append(
                "Formal invariant ledger entry hash mismatch: "
                f"{entry.get('ledger_entry_id')}."
            )
        if entry.get("claim_policy") != PROOF_OBLIGATION_CLAIM_POLICY:
            failures.append(
                "Formal invariant ledger claim policy drifted: "
                f"{entry.get('ledger_entry_id')}."
            )
        if entry.get("backend") != "lean4":
            failures.append("Formal invariant ledger entries must target Lean 4.")
        _verify_lean_source(entry, root, failures)


def _verify_lean_source(
    entry: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    _verify_nested_lean_source(
        entry,
        root,
        failures,
        label=str(entry.get("ledger_entry_id")),
    )


def _verify_nested_lean_source(
    entry: dict[str, Any],
    root: Path,
    failures: list[str],
    *,
    label: str,
) -> None:
    lean_source = entry.get("lean_source")
    if not isinstance(lean_source, dict):
        failures.append(f"Lean source is missing: {label}.")
        return
    path = lean_source.get("path")
    declaration = lean_source.get("declaration")
    if not isinstance(path, str) or not isinstance(declaration, str):
        failures.append(f"Lean source is incomplete: {label}.")
        return
    source_path = root / path
    try:
        raw = source_path.read_bytes()
    except FileNotFoundError:
        failures.append(f"Lean source is missing: {path}.")
        return
    if lean_source.get("sha256") != hashlib.sha256(raw).hexdigest():
        failures.append(f"Lean source hash mismatch: {path}.")
    if f"theorem {declaration}" not in raw.decode("utf-8"):
        failures.append(f"Lean theorem declaration is missing: {declaration}.")


def _verify_linked_artifacts(
    ledger: dict[str, Any],
    expected: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    linked = ledger.get("linked_artifacts")
    if not isinstance(linked, dict):
        failures.append("Formal obligation ledger linked_artifacts must be an object.")
        return
    if linked != expected["linked_artifacts"]:
        failures.append("Formal obligation ledger linked artifacts are not in sync.")
    for artifact_id, entry in linked.items():
        if not isinstance(entry, dict):
            failures.append(f"Linked artifact entry is invalid: {artifact_id}.")
            continue
        path = entry.get("path")
        if not isinstance(path, str):
            failures.append(f"Linked artifact path is missing: {artifact_id}.")
            continue
        try:
            current = _linked_artifact(Path(path), root=root)
        except FileNotFoundError:
            failures.append(f"Linked artifact is missing: {path}.")
            continue
        if entry != current:
            failures.append(f"Linked artifact hash drifted: {path}.")


def _ledger_sha256(ledger: dict[str, Any]) -> str:
    payload = {key: value for key, value in ledger.items() if key != "ledger_sha256"}
    return stable_sha256(payload)


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


def _list_or_empty(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []
