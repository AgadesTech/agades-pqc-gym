from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.integrations.lattice_estimator_manifest import (
    LATTICE_ESTIMATOR_REPOSITORY,
    build_lattice_estimator_manifest,
)
from agades_pqc_gym.validators.consistency import primary_attack_type

LATTICE_ESTIMATOR_BASELINE_CONTRACTS_SCHEMA = (
    "agades.pqc.lattice_estimator_baseline_contracts.v1"
)
LATTICE_ESTIMATOR_BASELINE_CONTRACTS_VERIFICATION_SCHEMA = (
    "agades.pqc.lattice_estimator_baseline_contracts_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
_CONTRACT_PATH_BY_ATTACK_TYPE = {
    "bounded_distance_decoding": "examples/attack_plans/lattice_bdd_toy.json",
    "bkw": "examples/attack_plans/lattice_bkw_toy.json",
    "dual_attack": "examples/attack_plans/lattice_dual_attack_toy.json",
    "dual_hybrid": "examples/attack_plans/lattice_dual_hybrid_toy.json",
    "primal_usvp": "examples/attack_plans/lattice_primal_usvp_toy.json",
}
_DISALLOWED_NUMERIC_REFERENCE_FIELDS = (
    "expected_memory_bits",
    "expected_success_probability",
    "expected_time_bits",
    "reference_memory_bits",
    "reference_success_probability",
    "reference_time_bits",
)


def build_lattice_estimator_baseline_contracts(
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    estimator_manifest = build_lattice_estimator_manifest()
    mappings = estimator_manifest["agades_boundary"]["reviewed_lwe_mappings"]
    pinned_commit = estimator_manifest["upstream"]["pinned_commit"]

    contracts = [
        _baseline_contract(project_root, attack_type, algorithm_key)
        for attack_type, algorithm_key in sorted(
            mappings.items(),
            key=lambda item: item[1],
        )
    ]

    return {
        "schema_version": LATTICE_ESTIMATOR_BASELINE_CONTRACTS_SCHEMA,
        "project": estimator_manifest["project"],
        "upstream": {
            "repository": LATTICE_ESTIMATOR_REPOSITORY,
            "pinned_commit": pinned_commit,
            "pin_source": "docs/lattice_estimator_manifest.json",
        },
        "baseline_policy": {
            "status": "review_contract_ready_not_reproduced",
            "numeric_reference_outputs_committed": False,
            "requires_matching_lattice_estimator_pin": True,
            "requires_expert_review_before_numeric_baselines": True,
            "security_claim": False,
            "publication_allowed": False,
        },
        "contracts": contracts,
        "release_gates": [
            "uv run pytest tests/test_lattice_estimator_baseline_contracts.py -q",
            "uv run agades-pqc lattice-estimator-baseline-contracts --out "
            "docs/lattice_estimator_baseline_contracts.json",
            "uv run agades-pqc lattice-estimator-baseline-contracts-verify "
            "--contracts docs/lattice_estimator_baseline_contracts.json",
            "uv run agades-pqc ecosystem-smoke-verify --report "
            "reports/ecosystem_smoke.json",
            "uv run agades-pqc release-audit --out public/release_audit.json",
        ],
    }


def write_lattice_estimator_baseline_contracts(
    out: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    contracts = build_lattice_estimator_baseline_contracts(root=root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(contracts, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return contracts


def verify_lattice_estimator_baseline_contracts(
    contracts_path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    contracts = _read_contracts(contracts_path, project_root, failures)
    expected = build_lattice_estimator_baseline_contracts(root=project_root)

    if contracts != expected:
        failures.append("Lattice Estimator baseline contracts are not in sync.")

    _verify_project(contracts, failures)
    _verify_upstream(contracts, failures)
    _verify_policy(contracts, failures)
    _verify_contract_entries(contracts, project_root, failures)
    _verify_release_gates(contracts, failures)

    return _verification_result(contracts_path, contracts, failures)


def _baseline_contract(
    root: Path,
    attack_type: str,
    algorithm_key: str,
) -> dict[str, Any]:
    source_path = _CONTRACT_PATH_BY_ATTACK_TYPE[attack_type]
    plan = AttackPlan.model_validate_json(
        (root / source_path).read_text(encoding="utf-8")
    )
    return {
        "attack_plan_id": plan.attack_plan_id,
        "attack_type": attack_type,
        "algorithm_key": algorithm_key,
        "source_path": source_path,
        "target_family": plan.target.family.value,
        "target_name": plan.target.name,
        "operator_types": [operator.type for operator in plan.operators],
        "numeric_reference_status": "pending_reviewed_reproduction",
        "required_reproduction_gate": "external_estimator_commit_matches_pin",
        "review_required_before_numeric_baseline": True,
        "security_claim": False,
    }


def _read_contracts(
    contracts_path: Path,
    root: Path,
    failures: list[str],
) -> dict[str, Any]:
    path = contracts_path if contracts_path.is_absolute() else root / contracts_path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(
            f"Lattice Estimator baseline contracts are missing: {contracts_path}."
        )
        return {}
    except json.JSONDecodeError as exc:
        failures.append(
            "Lattice Estimator baseline contracts are invalid JSON at line "
            f"{exc.lineno}."
        )
        return {}

    if not isinstance(payload, dict):
        failures.append("Lattice Estimator baseline contracts must be a JSON object.")
        return {}
    return payload


def _verify_project(contracts: dict[str, Any], failures: list[str]) -> None:
    expected_project = build_lattice_estimator_manifest()["project"]
    if contracts.get("schema_version") != LATTICE_ESTIMATOR_BASELINE_CONTRACTS_SCHEMA:
        failures.append(
            "Lattice Estimator baseline contracts schema_version must be "
            f"{LATTICE_ESTIMATOR_BASELINE_CONTRACTS_SCHEMA}."
        )
    if contracts.get("project") != expected_project:
        failures.append("Lattice Estimator baseline contracts project drifted.")


def _verify_upstream(contracts: dict[str, Any], failures: list[str]) -> None:
    expected_manifest = build_lattice_estimator_manifest()
    upstream = contracts.get("upstream")
    if not isinstance(upstream, dict):
        failures.append(
            "Lattice Estimator baseline contracts upstream must be an object."
        )
        return
    if upstream.get("repository") != LATTICE_ESTIMATOR_REPOSITORY:
        failures.append("Lattice Estimator baseline contracts repository drifted.")
    if upstream.get("pinned_commit") != expected_manifest["upstream"]["pinned_commit"]:
        failures.append("Lattice Estimator baseline contracts pin drifted.")
    if upstream.get("pin_source") != "docs/lattice_estimator_manifest.json":
        failures.append("Lattice Estimator baseline contracts pin source drifted.")


def _verify_policy(contracts: dict[str, Any], failures: list[str]) -> None:
    policy = contracts.get("baseline_policy")
    if not isinstance(policy, dict):
        failures.append(
            "Lattice Estimator baseline contracts baseline_policy must be an object."
        )
        return
    if policy.get("status") != "review_contract_ready_not_reproduced":
        failures.append("Baseline policy status drifted.")
    if policy.get("numeric_reference_outputs_committed") is not False:
        failures.append(
            "Baseline policy must not commit numeric reference outputs yet."
        )
    if policy.get("requires_matching_lattice_estimator_pin") is not True:
        failures.append(
            "Baseline policy must require the checked Lattice Estimator pin."
        )
    if policy.get("requires_expert_review_before_numeric_baselines") is not True:
        failures.append("Baseline policy must require expert review.")
    if policy.get("security_claim") is not False:
        failures.append("Baseline policy must not advertise security claims.")
    if policy.get("publication_allowed") is not False:
        failures.append("Baseline policy must keep publication blocked.")


def _verify_contract_entries(
    contracts: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    entries = contracts.get("contracts")
    if not isinstance(entries, list):
        failures.append("Lattice Estimator baseline contracts must include a list.")
        return

    expected_mappings = build_lattice_estimator_manifest()["agades_boundary"][
        "reviewed_lwe_mappings"
    ]
    observed_mappings: dict[str, str] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            failures.append(f"Lattice Estimator baseline contract {index} is invalid.")
            continue
        _verify_contract_entry(entry, index, root, failures)
        attack_type = entry.get("attack_type")
        algorithm_key = entry.get("algorithm_key")
        if isinstance(attack_type, str) and isinstance(algorithm_key, str):
            observed_mappings[attack_type] = algorithm_key

    if observed_mappings != expected_mappings:
        failures.append(
            "Lattice Estimator baseline contracts do not cover every reviewed "
            "LWE mapping."
        )


def _verify_contract_entry(
    entry: dict[str, Any],
    index: int,
    root: Path,
    failures: list[str],
) -> None:
    attack_type = entry.get("attack_type")
    source_path = entry.get("source_path")
    for field in _DISALLOWED_NUMERIC_REFERENCE_FIELDS:
        if field in entry:
            failures.append(
                f"Lattice Estimator baseline contract {index} must not contain {field}."
            )
    if entry.get("target_family") != "LWE":
        failures.append(
            f"Lattice Estimator baseline contract {index} must remain LWE-only."
        )
    if entry.get("numeric_reference_status") != "pending_reviewed_reproduction":
        failures.append(
            f"Lattice Estimator baseline contract {index} numeric status drifted."
        )
    if entry.get("required_reproduction_gate") != (
        "external_estimator_commit_matches_pin"
    ):
        failures.append(
            f"Lattice Estimator baseline contract {index} reproduction gate drifted."
        )
    if entry.get("review_required_before_numeric_baseline") is not True:
        failures.append(
            f"Lattice Estimator baseline contract {index} lacks review gate."
        )
    if entry.get("security_claim") is not False:
        failures.append(
            f"Lattice Estimator baseline contract {index} advertises a security claim."
        )
    if not isinstance(source_path, str):
        failures.append(
            f"Lattice Estimator baseline contract {index} source_path is invalid."
        )
        return

    path = root / source_path
    try:
        plan = AttackPlan.model_validate_json(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(
            f"Lattice Estimator baseline contract {index} source is missing."
        )
        return
    except Exception as exc:  # noqa: BLE001 - verifier reports malformed fixtures.
        failures.append(
            f"Lattice Estimator baseline contract {index} source is invalid: {exc}"
        )
        return

    if plan.attack_plan_id != entry.get("attack_plan_id"):
        failures.append(
            f"Lattice Estimator baseline contract {index} attack_plan_id drifted."
        )
    if primary_attack_type(plan) != attack_type:
        failures.append(
            f"Lattice Estimator baseline contract {index} attack_type drifted."
        )
    if plan.target.family.value != entry.get("target_family"):
        failures.append(
            f"Lattice Estimator baseline contract {index} target family drifted."
        )
    if plan.target.name != entry.get("target_name"):
        failures.append(
            f"Lattice Estimator baseline contract {index} target name drifted."
        )
    if [operator.type for operator in plan.operators] != entry.get("operator_types"):
        failures.append(
            f"Lattice Estimator baseline contract {index} operator types drifted."
        )


def _verify_release_gates(contracts: dict[str, Any], failures: list[str]) -> None:
    release_gates = contracts.get("release_gates")
    expected = build_lattice_estimator_baseline_contracts()["release_gates"]
    if not isinstance(release_gates, list):
        failures.append(
            "Lattice Estimator baseline contracts release_gates must be a list."
        )
        return
    for gate in expected:
        if gate not in release_gates:
            failures.append(
                f"Lattice Estimator baseline contract release gate missing: {gate}"
            )


def _verification_result(
    contracts_path: Path,
    contracts: dict[str, Any],
    failures: list[str],
) -> dict[str, Any]:
    entries = contracts.get("contracts", [])
    if not isinstance(entries, list):
        entries = []
    covered = sorted(
        [
            (entry.get("attack_type"), entry.get("algorithm_key"))
            for entry in entries
            if isinstance(entry, dict)
            and isinstance(entry.get("attack_type"), str)
            and isinstance(entry.get("algorithm_key"), str)
        ],
        key=lambda item: item[1],
    )
    policy = contracts.get("baseline_policy", {})
    if not isinstance(policy, dict):
        policy = {}
    upstream = contracts.get("upstream", {})
    if not isinstance(upstream, dict):
        upstream = {}

    return {
        "schema_version": LATTICE_ESTIMATOR_BASELINE_CONTRACTS_VERIFICATION_SCHEMA,
        "contracts_path": contracts_path.as_posix(),
        "accepted": not failures,
        "summary": {
            "contract_count": len(entries),
            "covered_algorithm_keys": [algorithm_key for _, algorithm_key in covered],
            "covered_attack_types": [attack_type for attack_type, _ in covered],
            "failure_count": len(failures),
            "numeric_reference_outputs_committed": policy.get(
                "numeric_reference_outputs_committed"
            ),
            "pinned_commit": upstream.get("pinned_commit"),
            "security_claim": policy.get("security_claim"),
        },
        "failures": failures,
    }
