from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from agades_pqc_gym.formal.obligation_ledger import (
    DEFAULT_OBLIGATION_LEDGER_PATH,
    build_formal_obligation_ledger,
)
from agades_pqc_gym.utils.hashing import stable_sha256

FORMAL_SMT_ASSIST_SCHEMA = "agades.pqc.formal.smt_assist_contract.v1"
FORMAL_SMT_ASSIST_VERIFICATION_SCHEMA = (
    "agades.pqc.formal.smt_assist_contract_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SMT_ASSIST_PATH = Path("docs/formal_smt_assist_contract.json")
ALLOWED_OBLIGATION_KINDS = [
    "target_invariant",
    "operator_precondition",
]
EXCLUDED_OBLIGATION_KINDS = [
    "schema_only_boundary",
    "family_applicability_boundary",
    "estimator_claim_boundary",
]
ALLOWED_THEORY_FRAGMENTS = [
    "quantifier_free_integer_arithmetic",
    "finite_enumeration_membership",
    "boolean_shape_constraints",
]
FORBIDDEN_USES = [
    "cryptographic_security_claim",
    "estimator_cost_model_validation",
    "replacement_for_lean_theorem",
    "replacement_for_crypto_domain_review",
    "public_claim_automation",
]
LINKED_ARTIFACT_PATHS = {
    "formal_lean_backend": "docs/formal_lean_backend.json",
    "formal_obligation_ledger": DEFAULT_OBLIGATION_LEDGER_PATH.as_posix(),
    "formal_operator_semantics": "docs/formal_operator_semantics.json",
    "formal_family_coverage": "docs/formal_family_coverage.json",
    "formal_estimator_model": "docs/formal_estimator_model.json",
}


def build_formal_smt_assist_contract(
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    ledger = build_formal_obligation_ledger(root=project_root)
    candidate_obligations = _candidate_obligations(ledger)
    excluded_obligations = _excluded_obligations(ledger)
    contract = {
        "schema_version": FORMAL_SMT_ASSIST_SCHEMA,
        "project": {
            "name": "Agades PQC Gym",
            "repository": "https://github.com/AgadesTech/agades-pqc-gym",
            "package": "agades_pqc_gym",
        },
        "backend_policy": {
            "primary_backend": "lean4",
            "primary_library": "mathlib",
            "assist_backend": "z3",
            "assist_role": "optional_secondary_check",
            "may_replace_primary_backend": False,
            "may_discharge_security_claims": False,
            "requires_lean_type_rule": True,
            "requires_reviewer_approval": True,
        },
        "scope": {
            "allowed_obligation_kinds": list(ALLOWED_OBLIGATION_KINDS),
            "excluded_obligation_kinds": list(EXCLUDED_OBLIGATION_KINDS),
            "allowed_theory_fragments": list(ALLOWED_THEORY_FRAGMENTS),
            "forbidden_uses": list(FORBIDDEN_USES),
        },
        "candidate_obligations": candidate_obligations,
        "excluded_obligations": excluded_obligations,
        "review_gate": {
            "status": "assist_contract_only",
            "z3_execution_required_for_public_release": False,
            "requires_lean_artifact_binding": True,
            "requires_formal_methods_reviewer": True,
            "requires_crypto_domain_reviewer_for_claims": True,
            "security_claim_allowed": False,
        },
        "linked_artifacts": _linked_artifacts(project_root),
        "summary": _summary(
            ledger,
            candidate_obligations=candidate_obligations,
            excluded_obligations=excluded_obligations,
        ),
        "release_gates": [
            "uv run pytest tests/test_formal_smt_assist.py -q",
            "uv run agades-pqc formal-smt-assist --out "
            "docs/formal_smt_assist_contract.json",
            "uv run agades-pqc formal-smt-assist-verify --contract "
            "docs/formal_smt_assist_contract.json",
            "uv run agades-pqc formal-obligation-ledger-verify --ledger "
            "docs/formal_obligation_ledger.json",
            "uv run agades-pqc formal-lean-backend-verify --backend "
            "docs/formal_lean_backend.json",
        ],
    }
    contract["contract_sha256"] = _contract_sha256(contract)
    return contract


def write_formal_smt_assist_contract(
    out: Path = DEFAULT_SMT_ASSIST_PATH,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    contract = build_formal_smt_assist_contract(root=project_root)
    resolved = _resolve_path(out, project_root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        json.dumps(contract, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return contract


def verify_formal_smt_assist_contract(
    contract_path: Path = DEFAULT_SMT_ASSIST_PATH,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    contract = _read_json_object(
        _resolve_path(contract_path, project_root),
        "Formal SMT assist contract",
        failures,
    )
    expected = build_formal_smt_assist_contract(root=project_root)

    if contract and contract != expected:
        failures.append("Formal SMT assist contract is not in sync.")
    if contract:
        _verify_schema(contract, failures)
        _verify_backend_policy(contract, failures)
        _verify_scope(contract, failures)
        _verify_candidate_obligations(contract, failures)
        _verify_excluded_obligations(contract, failures)
        _verify_review_gate(contract, failures)
        _verify_contract_hash(contract, failures)
        _verify_linked_artifacts(contract, expected, project_root, failures)

    return {
        "schema_version": FORMAL_SMT_ASSIST_VERIFICATION_SCHEMA,
        "contract_path": contract_path.as_posix(),
        "accepted": not failures,
        "summary": {
            "candidate_obligations": len(
                _list_or_empty(contract.get("candidate_obligations"))
            ),
            "excluded_obligations": len(
                _list_or_empty(contract.get("excluded_obligations"))
            ),
            "linked_artifacts": len(contract.get("linked_artifacts", {})),
            "failure_count": len(failures),
        },
        "failures": failures,
    }


def _candidate_obligations(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for obligation in _ledger_obligations(ledger):
        kind = obligation["obligation_type"]["kind"]
        if kind not in ALLOWED_OBLIGATION_KINDS:
            continue
        candidates.append(
            {
                "ledger_entry_id": obligation["ledger_entry_id"],
                "family": obligation["family"],
                "attack_plan_id": obligation["attack_plan_id"],
                "obligation_id": obligation["obligation_id"],
                "obligation_type": obligation["obligation_type"],
                "lean_theorem": obligation["lean_theorem"],
                "lean_source": obligation["lean_source"],
                "obligation_sha256": obligation["obligation_sha256"],
                "type_rule_sha256": obligation["type_rule"]["type_rule_sha256"],
                "smt_status": "candidate_not_encoded",
                "smt_role": "optional_secondary_finite_decidable_check",
                "claim_policy": {
                    "security_claim_allowed": False,
                    "requires_lean_theorem": True,
                    "requires_reviewer_approval": True,
                },
            }
        )
    return candidates


def _excluded_obligations(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    excluded: list[dict[str, Any]] = []
    for obligation in _ledger_obligations(ledger):
        kind = obligation["obligation_type"]["kind"]
        if kind not in EXCLUDED_OBLIGATION_KINDS:
            continue
        excluded.append(
            {
                "ledger_entry_id": obligation["ledger_entry_id"],
                "family": obligation["family"],
                "obligation_id": obligation["obligation_id"],
                "kind": kind,
                "reason": _excluded_reason(kind),
                "obligation_sha256": obligation["obligation_sha256"],
            }
        )
    return excluded


def _excluded_reason(kind: str) -> str:
    return {
        "schema_only_boundary": (
            "schema-only estimator boundaries are policy/review obligations"
        ),
        "family_applicability_boundary": (
            "family applicability requires cryptography domain review"
        ),
        "estimator_claim_boundary": (
            "estimator claim boundaries cannot be discharged by SMT"
        ),
    }[kind]


def _summary(
    ledger: dict[str, Any],
    *,
    candidate_obligations: list[dict[str, Any]],
    excluded_obligations: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_counter = Counter(
        candidate["obligation_type"]["kind"] for candidate in candidate_obligations
    )
    excluded_counter = Counter(
        excluded["kind"] for excluded in excluded_obligations
    )
    return {
        "total_obligations": len(_ledger_obligations(ledger)),
        "candidate_obligations": len(candidate_obligations),
        "excluded_obligations": len(excluded_obligations),
        "candidate_kinds": dict(sorted(candidate_counter.items())),
        "excluded_kinds": dict(sorted(excluded_counter.items())),
        "security_claim_allowed": False,
    }


def _verify_schema(contract: dict[str, Any], failures: list[str]) -> None:
    if contract.get("schema_version") != FORMAL_SMT_ASSIST_SCHEMA:
        failures.append(
            "Formal SMT assist contract schema_version must be "
            f"{FORMAL_SMT_ASSIST_SCHEMA}."
        )


def _verify_backend_policy(
    contract: dict[str, Any],
    failures: list[str],
) -> None:
    policy = _dict_or_empty(contract.get("backend_policy"))
    if policy.get("primary_backend") != "lean4":
        failures.append("SMT assistance primary backend must be Lean 4.")
    if policy.get("primary_library") != "mathlib":
        failures.append("SMT assistance primary library must be Mathlib.")
    if policy.get("assist_backend") != "z3":
        failures.append("SMT assistance backend must be Z3.")
    if policy.get("assist_role") != "optional_secondary_check":
        failures.append("SMT assistance role must be optional secondary check.")
    if policy.get("may_replace_primary_backend") is not False:
        failures.append("SMT assistance must not replace Lean 4 + Mathlib.")
    if policy.get("may_discharge_security_claims") is not False:
        failures.append("SMT assistance must not discharge security claims.")
    if policy.get("requires_lean_type_rule") is not True:
        failures.append("SMT assistance must require Lean type rules.")
    if policy.get("requires_reviewer_approval") is not True:
        failures.append("SMT assistance must require reviewer approval.")


def _verify_scope(contract: dict[str, Any], failures: list[str]) -> None:
    scope = _dict_or_empty(contract.get("scope"))
    if scope.get("allowed_obligation_kinds") != ALLOWED_OBLIGATION_KINDS:
        failures.append("SMT allowed obligation kinds are incorrect.")
    if scope.get("excluded_obligation_kinds") != EXCLUDED_OBLIGATION_KINDS:
        failures.append("SMT excluded obligation kinds are incorrect.")
    if scope.get("allowed_theory_fragments") != ALLOWED_THEORY_FRAGMENTS:
        failures.append("SMT allowed theory fragments are incorrect.")
    if scope.get("forbidden_uses") != FORBIDDEN_USES:
        failures.append("SMT forbidden uses are incorrect.")


def _verify_candidate_obligations(
    contract: dict[str, Any],
    failures: list[str],
) -> None:
    for candidate in _list_or_empty(contract.get("candidate_obligations")):
        if not isinstance(candidate, dict):
            failures.append("SMT candidate obligation must be an object.")
            continue
        obligation_type = _dict_or_empty(candidate.get("obligation_type"))
        kind = obligation_type.get("kind")
        if kind not in ALLOWED_OBLIGATION_KINDS:
            failures.append(
                "SMT candidate obligation uses a forbidden obligation kind: "
                f"{kind}."
            )
        if candidate.get("smt_status") != "candidate_not_encoded":
            failures.append("SMT candidate obligation status is incorrect.")
        if candidate.get("smt_role") != "optional_secondary_finite_decidable_check":
            failures.append("SMT candidate obligation role is incorrect.")
        claim_policy = _dict_or_empty(candidate.get("claim_policy"))
        if claim_policy.get("security_claim_allowed") is not False:
            failures.append("SMT candidate obligation must not allow claims.")
        if claim_policy.get("requires_lean_theorem") is not True:
            failures.append("SMT candidate obligation must require Lean theorem.")
        if claim_policy.get("requires_reviewer_approval") is not True:
            failures.append("SMT candidate obligation must require reviewer.")
        if not isinstance(candidate.get("lean_theorem"), str):
            failures.append("SMT candidate obligation must bind a Lean theorem.")
        if not _is_sha256(candidate.get("obligation_sha256")):
            failures.append("SMT candidate obligation hash is invalid.")
        if not _is_sha256(candidate.get("type_rule_sha256")):
            failures.append("SMT candidate type-rule hash is invalid.")


def _verify_excluded_obligations(
    contract: dict[str, Any],
    failures: list[str],
) -> None:
    for excluded in _list_or_empty(contract.get("excluded_obligations")):
        if not isinstance(excluded, dict):
            failures.append("SMT excluded obligation must be an object.")
            continue
        kind = excluded.get("kind")
        if kind not in EXCLUDED_OBLIGATION_KINDS:
            failures.append(f"SMT excluded obligation kind is incorrect: {kind}.")
        if not isinstance(excluded.get("reason"), str):
            failures.append("SMT excluded obligation must explain the reason.")
        if not _is_sha256(excluded.get("obligation_sha256")):
            failures.append("SMT excluded obligation hash is invalid.")


def _verify_review_gate(
    contract: dict[str, Any],
    failures: list[str],
) -> None:
    review_gate = _dict_or_empty(contract.get("review_gate"))
    expected = {
        "status": "assist_contract_only",
        "z3_execution_required_for_public_release": False,
        "requires_lean_artifact_binding": True,
        "requires_formal_methods_reviewer": True,
        "requires_crypto_domain_reviewer_for_claims": True,
        "security_claim_allowed": False,
    }
    if review_gate != expected:
        failures.append("SMT review gate is incorrect.")


def _verify_contract_hash(
    contract: dict[str, Any],
    failures: list[str],
) -> None:
    if contract.get("contract_sha256") != _contract_sha256(contract):
        failures.append("Formal SMT assist contract hash does not match payload.")


def _verify_linked_artifacts(
    contract: dict[str, Any],
    expected: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    linked = contract.get("linked_artifacts")
    if not isinstance(linked, dict):
        failures.append("Formal SMT assist linked_artifacts must be an object.")
        return
    if linked != expected.get("linked_artifacts"):
        failures.append("Formal SMT assist linked artifacts are not in sync.")
    for name, artifact in linked.items():
        if not isinstance(artifact, dict):
            failures.append(f"Formal SMT linked artifact {name} must be an object.")
            continue
        path = artifact.get("path")
        if not isinstance(path, str) or not path:
            failures.append(f"Formal SMT linked artifact {name} lacks path.")
            continue
        if not (root / path).is_file():
            failures.append(f"Formal SMT linked artifact missing: {name}.")
        if not _is_sha256(artifact.get("sha256")):
            failures.append(f"Formal SMT linked artifact lacks SHA: {name}.")


def _ledger_obligations(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        obligation
        for obligation in _list_or_empty(ledger.get("proof_obligations"))
        if isinstance(obligation, dict)
        and isinstance(obligation.get("obligation_type"), dict)
    ]


def _linked_artifacts(root: Path) -> dict[str, dict[str, str | None]]:
    return {
        name: {
            "path": path,
            "sha256": _file_sha256(root / path),
        }
        for name, path in LINKED_ARTIFACT_PATHS.items()
    }


def _contract_sha256(contract: dict[str, Any]) -> str:
    payload = {
        key: value for key, value in contract.items() if key != "contract_sha256"
    }
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


def _file_sha256(path: str | Path) -> str | None:
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except FileNotFoundError:
        return None


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def _list_or_empty(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
