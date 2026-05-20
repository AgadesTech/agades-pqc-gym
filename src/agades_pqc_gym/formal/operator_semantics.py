from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.core.operators import (
    ALLOWED_OPERATORS,
    LATTICE_OPERATORS,
    operator_required_param_schema,
    supported_operators_for_family,
)
from agades_pqc_gym.core.target import TargetFamily
from agades_pqc_gym.formal.artifacts import (
    BACKEND,
    LEAN_THEOREM_SOURCES,
    OPERATOR_SEMANTICS,
)
from agades_pqc_gym.integrations.family_operator_catalog import (
    build_family_operator_catalog,
)
from agades_pqc_gym.utils.hashing import stable_sha256

FORMAL_OPERATOR_SEMANTICS_SCHEMA = "agades.pqc.formal.operator_semantics.v1"
FORMAL_OPERATOR_SEMANTICS_VERIFICATION_SCHEMA = (
    "agades.pqc.formal.operator_semantics_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OPERATOR_SEMANTICS_PATH = Path("docs/formal_operator_semantics.json")
RUNTIME_CLAIM_BOUNDARY = (
    "operator semantics define AttackPlan applicability and routing, "
    "not cryptographic break evidence"
)
CLAIM_POLICY = {
    "security_claim_allowed_without_review": False,
    "proof_obligation_required_before_claim": True,
    "estimator_result_required_before_claim": True,
    "human_review_required_before_claim": True,
}
LINKED_ARTIFACT_PATHS = {
    "family_operator_catalog": "docs/family_operator_catalog.json",
    "family_plugin_manifest": "docs/family_plugin_manifest.json",
}
FORMAL_RULE_SPECS = (
    {
        "rule_id": "operator.required_params_present",
        "statement": (
            "The AttackPlan operator is only applicable when every required "
            "parameter declared by the operator schema is present."
        ),
        "lean_theorem": "AgadesPQC.OperatorSemantics.required_parameter_bound",
    },
    {
        "rule_id": "operator.family_binding_valid",
        "statement": (
            "The operator may only be routed through families listed in its "
            "AttackPlan family binding."
        ),
        "lean_theorem": "AgadesPQC.OperatorSemantics.family_binding_valid",
    },
    {
        "rule_id": "operator.unreviewed_security_claim_forbidden",
        "statement": (
            "Unreviewed operator semantics may support applicability and "
            "routing checks, but cannot authorize a cryptographic security "
            "claim."
        ),
        "lean_theorem": (
            "AgadesPQC.OperatorSemantics.unreviewed_security_claim_forbidden"
        ),
    },
)


def build_formal_operator_semantics(root: Path | None = None) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    family_catalog = build_family_operator_catalog(root=project_root)
    operators = [
        _operator_entry(
            operator,
            root=project_root,
            family_catalog=family_catalog,
        )
        for operator in OPERATOR_SEMANTICS
    ]
    semantics = {
        "schema_version": FORMAL_OPERATOR_SEMANTICS_SCHEMA,
        "project": {
            "name": "Agades PQC Gym",
            "repository": "https://github.com/AgadesTech/agades-pqc-gym",
            "package": "agades_pqc_gym",
        },
        "backend": dict(BACKEND),
        "claim_boundary": RUNTIME_CLAIM_BOUNDARY,
        "operators": operators,
        "summary": _summary(operators),
        "linked_artifacts": _linked_artifacts(project_root),
        "release_gates": [
            "uv run pytest tests/test_formal_operator_semantics.py -q",
            "uv run agades-pqc formal-operator-semantics --out "
            "docs/formal_operator_semantics.json",
            "uv run agades-pqc formal-operator-semantics-verify --semantics "
            "docs/formal_operator_semantics.json",
            "uv run agades-pqc family-operator-catalog-verify --catalog "
            "docs/family_operator_catalog.json",
        ],
    }
    semantics["semantics_sha256"] = _semantics_sha256(semantics)
    return semantics


def write_formal_operator_semantics(
    out: Path = DEFAULT_OPERATOR_SEMANTICS_PATH,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    semantics = build_formal_operator_semantics(root=project_root)
    resolved = _resolve_path(out, project_root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        json.dumps(semantics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return semantics


def verify_formal_operator_semantics(
    semantics_path: Path = DEFAULT_OPERATOR_SEMANTICS_PATH,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    semantics = _read_json_object(
        _resolve_path(semantics_path, project_root),
        "Formal operator semantics",
        failures,
    )
    expected = build_formal_operator_semantics(root=project_root)
    if semantics and semantics != expected:
        failures.append("Formal operator semantics are not in sync.")
    if semantics:
        _verify_semantics_shape(semantics, failures)
        _verify_semantics_hash(semantics, failures)
        _verify_operator_entries(semantics, project_root, failures)
        _verify_linked_artifacts(semantics, expected, project_root, failures)

    operators = [
        entry
        for entry in _list_or_empty(semantics.get("operators"))
        if isinstance(entry, dict)
    ]
    summary = {
        "operators": len(operators),
        "required_param_fields": sum(
            len(_dict_or_empty(entry.get("required_params"))) for entry in operators
        ),
        "linked_artifacts": len(semantics.get("linked_artifacts", {})),
        "failure_count": len(failures),
    }
    return {
        "schema_version": FORMAL_OPERATOR_SEMANTICS_VERIFICATION_SCHEMA,
        "semantics_path": semantics_path.as_posix(),
        "accepted": not failures,
        "summary": summary,
        "failures": failures,
    }


def operator_semantics_entry(operator_type: str) -> dict[str, str]:
    semantics_id, lean_namespace = OPERATOR_SEMANTICS[operator_type]
    return {
        "operator": operator_type,
        "semantics_id": semantics_id,
        "lean_namespace": lean_namespace,
    }


def _operator_entry(
    operator_type: str,
    *,
    root: Path = ROOT,
    family_catalog: dict[str, Any] | None = None,
) -> dict[str, Any]:
    catalog = family_catalog or build_family_operator_catalog(root=root)
    entry = {
        **operator_semantics_entry(operator_type),
        "required_params": operator_required_param_schema(operator_type),
        "formal_rules": _formal_rules(root),
        "attackplan_families": [
            family.value
            for family in TargetFamily
            if operator_type in supported_operators_for_family(family)
        ],
        "family_bindings": _family_bindings(operator_type, catalog),
        "runtime_claim_boundary": RUNTIME_CLAIM_BOUNDARY,
        "claim_policy": dict(CLAIM_POLICY),
    }
    entry["entry_sha256"] = _entry_sha256(entry)
    return entry


def _summary(operators: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "operators": len(operators),
        "lattice_operators": sum(
            1 for entry in operators if entry["operator"] in LATTICE_OPERATORS
        ),
        "non_lattice_operators": sum(
            1 for entry in operators if entry["operator"] not in LATTICE_OPERATORS
        ),
        "required_param_fields": sum(
            len(_dict_or_empty(entry.get("required_params"))) for entry in operators
        ),
        "attackplan_family_bindings": sum(
            len(_list_or_empty(entry.get("attackplan_families")))
            for entry in operators
        ),
        "applicability_validator_bindings": sum(
            len(_list_or_empty(entry.get("family_bindings"))) for entry in operators
        ),
        "schema_only_family_bindings": sum(
            1
            for entry in operators
            for binding in _list_or_empty(entry.get("family_bindings"))
            if isinstance(binding, dict) and binding.get("schema_only") is True
        ),
        "security_claim_allowed_without_review": sum(
            1
            for entry in operators
            if _dict_or_empty(entry.get("claim_policy")).get(
                "security_claim_allowed_without_review"
            )
        ),
    }


def _verify_semantics_shape(
    semantics: dict[str, Any],
    failures: list[str],
) -> None:
    if semantics.get("schema_version") != FORMAL_OPERATOR_SEMANTICS_SCHEMA:
        failures.append(
            "Formal operator semantics schema_version must be "
            f"{FORMAL_OPERATOR_SEMANTICS_SCHEMA}."
        )
    if semantics.get("backend") != BACKEND:
        failures.append("Formal operator semantics backend must be Lean 4 + Mathlib.")
    if semantics.get("claim_boundary") != RUNTIME_CLAIM_BOUNDARY:
        failures.append("Formal operator semantics claim boundary is incorrect.")
    operators = [
        entry
        for entry in _list_or_empty(semantics.get("operators"))
        if isinstance(entry, dict)
    ]
    if semantics.get("summary") != _summary(operators):
        failures.append("Formal operator semantics summary is inconsistent.")


def _verify_semantics_hash(
    semantics: dict[str, Any],
    failures: list[str],
) -> None:
    if semantics.get("semantics_sha256") != _semantics_sha256(semantics):
        failures.append("Formal operator semantics hash does not match its payload.")


def _verify_operator_entries(
    semantics: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    entries = _list_or_empty(semantics.get("operators"))
    expected_operators = list(OPERATOR_SEMANTICS)
    if [
        entry.get("operator") for entry in entries if isinstance(entry, dict)
    ] != expected_operators:
        failures.append(
            "Formal operator semantics must cover every ALLOWED_OPERATORS entry."
        )
    if set(expected_operators) != set(ALLOWED_OPERATORS):
        failures.append("OPERATOR_SEMANTICS and ALLOWED_OPERATORS are out of sync.")
    for raw_entry in entries:
        if not isinstance(raw_entry, dict):
            failures.append("Formal operator semantics entry must be an object.")
            continue
        _verify_operator_entry(raw_entry, root, failures)


def _verify_operator_entry(
    entry: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    operator = entry.get("operator")
    if not isinstance(operator, str) or operator not in ALLOWED_OPERATORS:
        failures.append(
            f"Formal operator semantics operator is unsupported: {operator}."
        )
        return
    expected = _operator_entry(operator, root=root)
    if entry.get("semantics_id") != expected["semantics_id"]:
        failures.append("Formal operator semantics IDs are not in sync.")
    if entry.get("lean_namespace") != expected["lean_namespace"]:
        failures.append("Formal operator semantics Lean namespaces are not in sync.")
    if entry.get("required_params") != expected["required_params"]:
        failures.append("Formal operator semantics parameter schemas are not in sync.")
    if entry.get("formal_rules") != expected["formal_rules"]:
        failures.append("Formal operator semantics formal rules are not in sync.")
    if entry.get("attackplan_families") != expected["attackplan_families"]:
        failures.append("Formal operator semantics family bindings are not in sync.")
    if entry.get("family_bindings") != expected["family_bindings"]:
        failures.append(
            "Formal operator semantics family validator bindings are not in sync."
        )
    if entry.get("runtime_claim_boundary") != RUNTIME_CLAIM_BOUNDARY:
        failures.append("Formal operator semantics claim boundary is incorrect.")
    claim_policy = _dict_or_empty(entry.get("claim_policy"))
    if claim_policy.get("security_claim_allowed_without_review") is not False:
        failures.append(
            "Formal operator semantics must not allow unreviewed security claims."
        )
    if claim_policy != CLAIM_POLICY:
        failures.append("Formal operator semantics claim policy is not in sync.")
    if entry.get("entry_sha256") != _entry_sha256(entry):
        failures.append(f"Formal operator semantics entry hash mismatch: {operator}.")


def _verify_linked_artifacts(
    semantics: dict[str, Any],
    expected: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    linked = semantics.get("linked_artifacts")
    if not isinstance(linked, dict):
        failures.append("Formal operator semantics linked_artifacts must be an object.")
        return
    if linked != expected.get("linked_artifacts"):
        failures.append(
            "Formal operator semantics linked artifact hashes are not in sync."
        )
    for name, artifact in linked.items():
        if not isinstance(artifact, dict):
            failures.append(
                f"Formal operator semantics linked artifact {name} invalid."
            )
            continue
        path = artifact.get("path")
        if not isinstance(path, str) or not (root / path).is_file():
            failures.append(
                f"Formal operator semantics linked artifact missing: {name}."
            )
        if artifact.get("sha256") is None:
            failures.append(
                f"Formal operator semantics linked artifact lacks SHA: {name}."
            )


def _semantics_sha256(semantics: dict[str, Any]) -> str:
    payload = {
        key: value
        for key, value in semantics.items()
        if key != "semantics_sha256"
    }
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


def _formal_rules(root: Path) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    for spec in FORMAL_RULE_SPECS:
        theorem = spec["lean_theorem"]
        source_path = LEAN_THEOREM_SOURCES[theorem]
        rules.append(
            {
                **spec,
                "lean_source": {
                    "path": source_path,
                    "sha256": _file_sha256(root / source_path),
                },
            }
        )
    return rules


def _family_bindings(
    operator_type: str,
    family_catalog: dict[str, Any],
) -> list[dict[str, Any]]:
    catalog_entries = {
        entry["family"]: entry
        for entry in _list_or_empty(family_catalog.get("families"))
        if isinstance(entry, dict) and isinstance(entry.get("family"), str)
    }
    bindings: list[dict[str, Any]] = []
    for family in TargetFamily:
        if operator_type not in supported_operators_for_family(family):
            continue
        catalog_entry = catalog_entries[family.value]
        operators = [
            operator
            for operator in _list_or_empty(catalog_entry.get("operators"))
            if (
                isinstance(operator, dict)
                and operator.get("operator_type") == operator_type
            )
        ]
        support_statuses = sorted(
            {
                status
                for operator in operators
                if isinstance(status := operator.get("support_status"), str)
            }
        )
        support_level = catalog_entry["support_level"]
        bindings.append(
            {
                "family": family.value,
                "plugin": catalog_entry["plugin"],
                "support_level": support_level,
                "applicability_validator": catalog_entry[
                    "applicability_validator"
                ],
                "catalog_operator_entry_count": len(operators),
                "catalog_support_statuses": support_statuses,
                "schema_only": support_level == "schema_only",
            }
        )
    return bindings


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
