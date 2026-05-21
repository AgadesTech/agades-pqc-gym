from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.operators import ALLOWED_OPERATORS
from agades_pqc_gym.core.target import TargetFamily
from agades_pqc_gym.formal.artifacts import (
    ATTACK_PLAN_CANONICALIZATION,
    ATTACK_PLAN_SCHEMA_CONTRACT_SCHEMA,
    ATTACK_PLAN_SCHEMA_MODEL,
    ATTACK_PLAN_VALIDATION,
    BACKEND,
)
from agades_pqc_gym.formal.lean_backend import DEFAULT_BACKEND_PATH
from agades_pqc_gym.formal.operator_semantics import (
    DEFAULT_OPERATOR_SEMANTICS_PATH,
)
from agades_pqc_gym.utils.hashing import stable_sha256

FORMAL_ATTACKPLAN_SEMANTICS_SCHEMA = (
    "agades.pqc.formal.attackplan_semantics.v1"
)
FORMAL_ATTACKPLAN_SEMANTICS_VERIFICATION_SCHEMA = (
    "agades.pqc.formal.attackplan_semantics_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ATTACKPLAN_SEMANTICS_PATH = Path(
    "docs/formal_attackplan_semantics.json"
)
LEAN_SOURCE_PATH = Path("formal/lean/AgadesPQC/AttackPlan.lean")
CLAIM_POLICY = {
    "public_interpretation": "schema_applicability_and_review_gate_only",
    "security_claim_allowed_without_review": False,
    "estimator_result_required_before_claim": True,
    "proof_obligation_required_before_claim": True,
    "human_review_required_before_claim": True,
}
VALIDATION_RULES = (
    {
        "rule_id": "attackplan.json_schema_valid",
        "runtime_enforcement": "AttackPlan.model_validate_json",
        "statement": "AttackPlan input must validate against the versioned schema.",
    },
    {
        "rule_id": "attackplan.extra_fields_forbidden",
        "runtime_enforcement": "pydantic_config_extra_forbid",
        "statement": "Unknown fields are rejected at every AttackPlan schema level.",
    },
    {
        "rule_id": "attackplan.canonical_digest_stable",
        "runtime_enforcement": ATTACK_PLAN_CANONICALIZATION,
        "statement": (
            "Accepted AttackPlan JSON receives a stable canonical SHA-256 digest."
        ),
    },
    {
        "rule_id": "attackplan.operator_type_known",
        "runtime_enforcement": "AttackOperator.operator_type_must_be_known",
        "statement": "Every operator type must be declared in ALLOWED_OPERATORS.",
    },
    {
        "rule_id": "attackplan.operator_params_declared",
        "runtime_enforcement": "validate_operator_params",
        "statement": "Every operator parameter must satisfy its declared schema.",
    },
    {
        "rule_id": "attackplan.family_operator_supported",
        "runtime_enforcement": "AttackPlan.validate_cross_field_rules",
        "statement": (
            "Every operator must be supported by the AttackPlan target family."
        ),
    },
    {
        "rule_id": "attackplan.claims_review_gated",
        "runtime_enforcement": "Claims.require_source_for_pre_evaluation_claims",
        "statement": (
            "Pre-evaluation claims need an external source and remain gated by "
            "proof obligations, estimator binding, and human review."
        ),
    },
)
FORMAL_RULE_SPECS = (
    {
        "rule_id": "attackplan.schema_contract_well_formed",
        "statement": (
            "The public AttackPlan semantics contract requires schema validation, "
            "canonicalization, strict fields, supported operators, and claim gating."
        ),
        "lean_theorem": "AgadesPQC.AttackPlan.schema_contract_well_formed",
    },
    {
        "rule_id": "attackplan.canonicalization_stable",
        "statement": (
            "Canonicalized AttackPlan JSON is bound to a stable digest before "
            "proof obligations or evaluator results are attached."
        ),
        "lean_theorem": "AgadesPQC.AttackPlan.canonicalization_stable",
    },
    {
        "rule_id": "attackplan.operators_nonempty",
        "statement": "An accepted AttackPlan has at least one operator.",
        "lean_theorem": "AgadesPQC.AttackPlan.operators_nonempty",
    },
    {
        "rule_id": "attackplan.unsupported_operator_rejected",
        "statement": (
            "An operator unsupported by the target family makes the AttackPlan "
            "invalid instead of becoming an unreviewed family claim."
        ),
        "lean_theorem": "AgadesPQC.AttackPlan.unsupported_operator_rejected",
    },
    {
        "rule_id": "attackplan.unreviewed_security_claim_forbidden",
        "statement": (
            "Pending-review AttackPlan semantics cannot authorize a "
            "cryptographic security claim."
        ),
        "lean_theorem": (
            "AgadesPQC.AttackPlan.unreviewed_security_claim_forbidden"
        ),
    },
)
LINKED_ARTIFACT_PATHS = {
    "formal_lean_backend": DEFAULT_BACKEND_PATH.as_posix(),
    "formal_operator_semantics": DEFAULT_OPERATOR_SEMANTICS_PATH.as_posix(),
    "family_operator_catalog": "docs/family_operator_catalog.json",
    "family_plugin_manifest": "docs/family_plugin_manifest.json",
}


def build_formal_attackplan_semantics(
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    validation_rules = [dict(rule) for rule in VALIDATION_RULES]
    formal_rules = [_formal_rule(rule, project_root) for rule in FORMAL_RULE_SPECS]
    contract = {
        "schema_version": FORMAL_ATTACKPLAN_SEMANTICS_SCHEMA,
        "project": {
            "name": "Agades PQC Gym",
            "repository": "https://github.com/AgadesTech/agades-pqc-gym",
            "package": "agades_pqc_gym",
        },
        "backend": dict(BACKEND),
        "attack_plan_schema": _attack_plan_schema_contract(),
        "canonicalization": {
            "algorithm": ATTACK_PLAN_CANONICALIZATION,
            "hash": "stable_sha256",
            "purpose": (
                "bind semantically identical AttackPlan JSON to a stable digest"
            ),
        },
        "validation_rules": validation_rules,
        "formal_rules": formal_rules,
        "claim_policy": dict(CLAIM_POLICY),
        "linked_artifacts": _linked_artifacts(project_root),
        "summary": _summary(
            validation_rules=validation_rules,
            formal_rules=formal_rules,
        ),
        "release_gates": [
            "uv run pytest tests/test_formal_attackplan_semantics.py -q",
            "uv run agades-pqc formal-attackplan-semantics --out "
            "docs/formal_attackplan_semantics.json",
            "uv run agades-pqc formal-attackplan-semantics-verify --semantics "
            "docs/formal_attackplan_semantics.json",
            "uv run agades-pqc formal-operator-semantics-verify --semantics "
            "docs/formal_operator_semantics.json",
            "uv run agades-pqc formal-lean-backend-verify --backend "
            "docs/formal_lean_backend.json",
        ],
    }
    contract["semantics_sha256"] = _semantics_sha256(contract)
    return contract


def write_formal_attackplan_semantics(
    out: Path = DEFAULT_ATTACKPLAN_SEMANTICS_PATH,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    contract = build_formal_attackplan_semantics(root=project_root)
    resolved = _resolve_path(out, project_root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        json.dumps(contract, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return contract


def verify_formal_attackplan_semantics(
    semantics_path: Path = DEFAULT_ATTACKPLAN_SEMANTICS_PATH,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    contract = _read_json_object(
        _resolve_path(semantics_path, project_root),
        "Formal AttackPlan semantics",
        failures,
    )
    expected = build_formal_attackplan_semantics(root=project_root)

    if contract and contract != expected:
        failures.append("Formal AttackPlan semantics are not in sync.")
    if contract:
        _verify_schema(contract, failures)
        _verify_backend(contract, failures)
        _verify_attack_plan_schema(contract, failures)
        _verify_canonicalization(contract, failures)
        _verify_validation_rules(contract, failures)
        _verify_formal_rules(contract, project_root, failures)
        _verify_claim_policy(contract, failures)
        _verify_semantics_hash(contract, failures)
        _verify_linked_artifacts(contract, expected, project_root, failures)

    return {
        "schema_version": FORMAL_ATTACKPLAN_SEMANTICS_VERIFICATION_SCHEMA,
        "semantics_path": semantics_path.as_posix(),
        "accepted": not failures,
        "summary": {
            "validation_rules": len(
                _list_or_empty(contract.get("validation_rules"))
            ),
            "formal_rules": len(_list_or_empty(contract.get("formal_rules"))),
            "linked_artifacts": len(contract.get("linked_artifacts", {})),
            "failure_count": len(failures),
        },
        "failures": failures,
    }


def _attack_plan_schema_contract() -> dict[str, str]:
    return {
        "schema_version": ATTACK_PLAN_SCHEMA_CONTRACT_SCHEMA,
        "model": ATTACK_PLAN_SCHEMA_MODEL,
        "json_schema_sha256": stable_sha256(AttackPlan.model_json_schema()),
        "canonicalization": ATTACK_PLAN_CANONICALIZATION,
        "validation": ATTACK_PLAN_VALIDATION,
    }


def _formal_rule(
    rule: dict[str, str],
    root: Path,
) -> dict[str, Any]:
    source = _lean_source(root, rule["lean_theorem"])
    entry = {**rule, "lean_source": source}
    entry["rule_sha256"] = stable_sha256(entry)
    return entry


def _lean_source(root: Path, theorem: str) -> dict[str, str]:
    path = root / LEAN_SOURCE_PATH
    declaration = theorem.rsplit(".", 1)[-1]
    return {
        "path": LEAN_SOURCE_PATH.as_posix(),
        "declaration": declaration,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _summary(
    *,
    validation_rules: list[dict[str, Any]],
    formal_rules: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "required_fields": len(AttackPlan.model_json_schema()["required"]),
        "operators": len(ALLOWED_OPERATORS),
        "families": len(TargetFamily),
        "validation_rules": len(validation_rules),
        "formal_rules": len(formal_rules),
        "linked_artifacts": len(LINKED_ARTIFACT_PATHS),
        "security_claim_allowed_without_review": False,
    }


def _verify_schema(contract: dict[str, Any], failures: list[str]) -> None:
    if contract.get("schema_version") != FORMAL_ATTACKPLAN_SEMANTICS_SCHEMA:
        failures.append(
            "Formal AttackPlan semantics schema_version must be "
            f"{FORMAL_ATTACKPLAN_SEMANTICS_SCHEMA}."
        )


def _verify_backend(contract: dict[str, Any], failures: list[str]) -> None:
    if contract.get("backend") != BACKEND:
        failures.append("Formal AttackPlan semantics backend must be Lean 4 + Mathlib.")


def _verify_attack_plan_schema(
    contract: dict[str, Any],
    failures: list[str],
) -> None:
    if contract.get("attack_plan_schema") != _attack_plan_schema_contract():
        failures.append("AttackPlan schema contract is not in sync.")


def _verify_canonicalization(
    contract: dict[str, Any],
    failures: list[str],
) -> None:
    if contract.get("canonicalization") != {
        "algorithm": ATTACK_PLAN_CANONICALIZATION,
        "hash": "stable_sha256",
        "purpose": "bind semantically identical AttackPlan JSON to a stable digest",
    }:
        failures.append("AttackPlan canonicalization contract is incorrect.")


def _verify_validation_rules(
    contract: dict[str, Any],
    failures: list[str],
) -> None:
    rules = contract.get("validation_rules")
    if rules != [dict(rule) for rule in VALIDATION_RULES]:
        failures.append("AttackPlan validation rules are not in sync.")


def _verify_formal_rules(
    contract: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    rules = _list_or_empty(contract.get("formal_rules"))
    expected_rule_ids = {rule["rule_id"] for rule in FORMAL_RULE_SPECS}
    found_rule_ids = {
        rule.get("rule_id") for rule in rules if isinstance(rule, dict)
    }
    if found_rule_ids != expected_rule_ids:
        failures.append("AttackPlan formal rules are incomplete.")
    for rule in rules:
        if not isinstance(rule, dict):
            failures.append("AttackPlan formal rule must be an object.")
            continue
        theorem = rule.get("lean_theorem")
        if not isinstance(theorem, str) or not theorem.startswith(
            "AgadesPQC.AttackPlan."
        ):
            failures.append("AttackPlan formal rule must bind an AttackPlan theorem.")
        source = _dict_or_empty(rule.get("lean_source"))
        path = source.get("path")
        declaration = source.get("declaration")
        if path != LEAN_SOURCE_PATH.as_posix():
            failures.append("AttackPlan formal rule uses the wrong Lean source.")
            continue
        source_path = root / path
        if not source_path.is_file():
            failures.append("AttackPlan Lean source is missing.")
            continue
        raw = source_path.read_text(encoding="utf-8")
        if hashlib.sha256(raw.encode("utf-8")).hexdigest() != source.get("sha256"):
            failures.append("AttackPlan Lean source hash is invalid.")
        if not isinstance(declaration, str) or f"theorem {declaration}" not in raw:
            failures.append("AttackPlan Lean theorem declaration is missing.")
        if rule.get("rule_sha256") != stable_sha256(
            {key: value for key, value in rule.items() if key != "rule_sha256"}
        ):
            failures.append("AttackPlan formal rule hash is invalid.")


def _verify_claim_policy(
    contract: dict[str, Any],
    failures: list[str],
) -> None:
    policy = _dict_or_empty(contract.get("claim_policy"))
    if policy != CLAIM_POLICY:
        failures.append("AttackPlan claim policy is incorrect.")
    if policy.get("security_claim_allowed_without_review") is not False:
        failures.append("AttackPlan semantics must forbid unreviewed security claims.")


def _verify_semantics_hash(contract: dict[str, Any], failures: list[str]) -> None:
    if contract.get("semantics_sha256") != _semantics_sha256(contract):
        failures.append("Formal AttackPlan semantics hash does not match payload.")


def _verify_linked_artifacts(
    contract: dict[str, Any],
    expected: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    linked = contract.get("linked_artifacts")
    if not isinstance(linked, dict):
        failures.append(
            "Formal AttackPlan semantics linked_artifacts must be an object."
        )
        return
    if linked != expected.get("linked_artifacts"):
        failures.append("Formal AttackPlan semantics linked artifacts are not in sync.")
    for name, artifact in linked.items():
        if not isinstance(artifact, dict):
            failures.append(f"AttackPlan linked artifact {name} must be an object.")
            continue
        path = artifact.get("path")
        if not isinstance(path, str) or not path:
            failures.append(f"AttackPlan linked artifact {name} lacks path.")
            continue
        if not (root / path).is_file():
            failures.append(f"AttackPlan linked artifact missing: {name}.")
        if not _is_sha256(artifact.get("sha256")):
            failures.append(f"AttackPlan linked artifact lacks SHA: {name}.")


def _linked_artifacts(root: Path) -> dict[str, dict[str, str | None]]:
    return {
        name: {
            "path": path,
            "sha256": _file_sha256(root / path),
        }
        for name, path in LINKED_ARTIFACT_PATHS.items()
    }


def _semantics_sha256(contract: dict[str, Any]) -> str:
    payload = {
        key: value for key, value in contract.items() if key != "semantics_sha256"
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
