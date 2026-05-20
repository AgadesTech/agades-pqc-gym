from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path, PurePath
from typing import Any

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.evaluators.base import EstimatorAdapter
from agades_pqc_gym.evaluators.lattice_estimator import (
    LATTICE_ESTIMATOR_PINNED_COMMIT,
)
from agades_pqc_gym.evolution.scheduler import validate_policy_private_path
from agades_pqc_gym.integrations.lattice_estimator_baseline_contracts import (
    LATTICE_ESTIMATOR_BASELINE_CONTRACTS_SCHEMA,
    verify_lattice_estimator_baseline_contracts,
)
from agades_pqc_gym.integrations.lattice_estimator_manifest import (
    LATTICE_ESTIMATOR_REPOSITORY,
)
from agades_pqc_gym.utils.hashing import stable_sha256

LATTICE_ESTIMATOR_BASELINE_RUN_SCHEMA = (
    "agades.pqc.lattice_estimator_baseline_run.v1"
)
LATTICE_ESTIMATOR_BASELINE_RUN_VERIFICATION_SCHEMA = (
    "agades.pqc.lattice_estimator_baseline_run_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BASELINE_RUN_PATH = Path(
    "private/reports/lattice_estimator_baseline_run.json"
)


def build_lattice_estimator_baseline_run(
    *,
    contracts_path: Path,
    adapter: EstimatorAdapter,
    root: Path | None = None,
    report_path: Path | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    resolved_contracts_path = _resolve_path(contracts_path, project_root)
    contracts = _load_verified_contracts(contracts_path, project_root)
    contract_entries = _contract_entries(contracts)
    results = [
        _evaluate_contract(entry, adapter=adapter, project_root=project_root)
        for entry in contract_entries
    ]
    summary = _summary(results)

    return {
        "schema_version": LATTICE_ESTIMATOR_BASELINE_RUN_SCHEMA,
        "run_id": run_id or "manual-lattice-estimator-baseline-run",
        "created_at": "manual-baseline-run-recorded",
        "report": {
            "path": (report_path or DEFAULT_BASELINE_RUN_PATH).as_posix(),
            "private": True,
        },
        "contracts": {
            "path": contracts_path.as_posix(),
            "schema_version": contracts["schema_version"],
            "sha256": _sha256_file(resolved_contracts_path),
            "contract_count": len(contract_entries),
        },
        "upstream": {
            "repository": LATTICE_ESTIMATOR_REPOSITORY,
            "pinned_commit": LATTICE_ESTIMATOR_PINNED_COMMIT,
            "pin_source": "docs/lattice_estimator_manifest.json",
        },
        "baseline_policy": {
            "numeric_reference_outputs_committed": False,
            "private_numeric_outputs": True,
            "publication_allowed": False,
            "requires_expert_review_before_publication": True,
            "security_claim": False,
        },
        "results": results,
        "summary": summary,
        "safety": {
            "arbitrary_candidate_code_execution": False,
            "external_network_access": False,
            "lwe_only": True,
            "numeric_reference_outputs_committed": False,
            "publishes_numeric_references": False,
            "raw_estimator_output_committed": False,
            "review_required_before_publication": True,
            "writes_only_allowed_private_roots": True,
        },
    }


def write_lattice_estimator_baseline_run(
    out: Path,
    *,
    contracts_path: Path,
    policy: dict[str, Any],
    adapter: EstimatorAdapter,
    contracts_root: Path | None = None,
    policy_root: Path | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    output_root = (policy_root or ROOT).resolve()
    validate_policy_private_path(out, policy=policy, root=output_root)
    report = build_lattice_estimator_baseline_run(
        contracts_path=contracts_path,
        adapter=adapter,
        root=contracts_root,
        report_path=out,
        run_id=run_id,
    )
    resolved_out = _resolve_path(out, output_root)
    resolved_out.parent.mkdir(parents=True, exist_ok=True)
    resolved_out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def verify_lattice_estimator_baseline_run(
    report_path: Path,
    *,
    contracts_root: Path | None = None,
) -> dict[str, Any]:
    root = (contracts_root or ROOT).resolve()
    failures: list[str] = []
    report = _load_report(report_path, failures)
    summary = {
        "all_successful_results_from_pinned_commit": False,
        "contract_count": 0,
        "failure_count": 0,
        "lwe_only": False,
        "numeric_result_count": 0,
        "ok_results": 0,
        "private_report": None,
        "public_release_ok": None,
        "raw_output_digest_count": 0,
        "security_claim": None,
    }

    if report is not None:
        _verify_report_schema(report, failures)
        _verify_report_reference(report, failures, summary)
        expected_contracts = _verify_contract_reference(report, root, failures)
        _verify_baseline_policy(report, failures)
        _verify_safety(report, failures, summary)
        results = _verify_results(report, expected_contracts, failures)
        _verify_summary(report, results, failures, summary)
        _verify_no_private_payload_leakage(report, failures)

    summary["failure_count"] = len(failures)
    return {
        "schema_version": LATTICE_ESTIMATOR_BASELINE_RUN_VERIFICATION_SCHEMA,
        "report_path": report_path.as_posix(),
        "accepted": not failures,
        "summary": summary,
        "failures": failures,
    }


def _load_verified_contracts(
    contracts_path: Path,
    project_root: Path,
) -> dict[str, Any]:
    verification = verify_lattice_estimator_baseline_contracts(
        contracts_path,
        root=project_root,
    )
    if not verification["accepted"]:
        failures = "; ".join(verification["failures"])
        raise ValueError(
            "Lattice Estimator baseline contracts failed verification: "
            f"{failures}"
        )
    contracts = json.loads(
        _resolve_path(contracts_path, project_root).read_text(encoding="utf-8")
    )
    if contracts.get("schema_version") != LATTICE_ESTIMATOR_BASELINE_CONTRACTS_SCHEMA:
        raise ValueError("Lattice Estimator baseline contracts schema drifted.")
    return contracts


def _contract_entries(contracts: dict[str, Any]) -> list[dict[str, Any]]:
    entries = contracts.get("contracts")
    if not isinstance(entries, list):
        raise ValueError("Lattice Estimator baseline contracts must contain a list.")
    typed_entries: list[dict[str, Any]] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"Lattice Estimator baseline contract {index} is invalid.")
        typed_entries.append(entry)
    return typed_entries


def _evaluate_contract(
    entry: dict[str, Any],
    *,
    adapter: EstimatorAdapter,
    project_root: Path,
) -> dict[str, Any]:
    source_path = _string_field(entry, "source_path")
    plan = AttackPlan.model_validate_json(
        _resolve_path(Path(source_path), project_root).read_text(encoding="utf-8")
    )
    result = adapter.estimate(plan)
    if (
        result.evaluation_status == "ok"
        and result.estimator_commit != LATTICE_ESTIMATOR_PINNED_COMMIT
    ):
        raise ValueError(
            "Lattice Estimator baseline run produced a successful result from "
            "an unreviewed commit."
        )

    numeric_output_private = (
        result.evaluation_status == "ok"
        and result.time_bits is not None
        and result.memory_bits is not None
    )
    return {
        "attack_plan_id": _string_field(entry, "attack_plan_id"),
        "attack_type": _string_field(entry, "attack_type"),
        "algorithm_key": _string_field(entry, "algorithm_key"),
        "source_path": source_path,
        "target_family": _string_field(entry, "target_family"),
        "target_name": _string_field(entry, "target_name"),
        "evaluation_status": result.evaluation_status,
        "estimator_name": result.estimator_name,
        "estimator_version": result.estimator_version,
        "estimator_commit": result.estimator_commit,
        "commit_matches_pin": result.estimator_commit
        == LATTICE_ESTIMATOR_PINNED_COMMIT,
        "time_bits": result.time_bits if numeric_output_private else None,
        "memory_bits": result.memory_bits if numeric_output_private else None,
        "numeric_output_private": numeric_output_private,
        "public_reference_output": False,
        "raw_output_sha256": stable_sha256(result.raw_output),
        "warnings": list(result.warnings),
    }


def _summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    ok_results = _count_status(results, "ok")
    return {
        "all_successful_results_from_pinned_commit": all(
            result.get("commit_matches_pin")
            for result in results
            if result.get("evaluation_status") == "ok"
        )
        and ok_results > 0,
        "contract_count": len(results),
        "error_results": _count_status(results, "error"),
        "numeric_result_count": sum(
            1 for result in results if result.get("numeric_output_private") is True
        ),
        "ok_results": ok_results,
        "public_release_ok": False,
        "security_claim": False,
        "unsupported_results": _count_status(results, "unsupported"),
    }


def _count_status(results: list[dict[str, Any]], status: str) -> int:
    return sum(1 for result in results if result.get("evaluation_status") == status)


def _string_field(entry: dict[str, Any], field: str) -> str:
    value = entry.get(field)
    if not isinstance(value, str):
        raise ValueError(
            f"Lattice Estimator baseline contract field {field} is invalid."
        )
    return value


def _resolve_path(path: Path, root: Path) -> Path:
    return path if path.is_absolute() else root / path


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _load_report(path: Path, failures: list[str]) -> dict[str, Any] | None:
    if not path.exists():
        failures.append(f"Lattice Estimator baseline run report is missing: {path}.")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(
            "Lattice Estimator baseline run report is invalid JSON at line "
            f"{exc.lineno}: {exc.msg}."
        )
        return None
    if not isinstance(payload, dict):
        failures.append("Lattice Estimator baseline run report must be a JSON object.")
        return None
    return payload


def _verify_report_schema(report: dict[str, Any], failures: list[str]) -> None:
    if report.get("schema_version") != LATTICE_ESTIMATOR_BASELINE_RUN_SCHEMA:
        failures.append("Lattice Estimator baseline run schema drifted.")
    if not isinstance(report.get("run_id"), str) or not report["run_id"]:
        failures.append("Lattice Estimator baseline run run_id is invalid.")


def _verify_report_reference(
    report: dict[str, Any],
    failures: list[str],
    summary: dict[str, Any],
) -> None:
    report_ref = _dict_or_empty(report.get("report"))
    summary["private_report"] = report_ref.get("private")
    if report_ref.get("private") is not True:
        failures.append("Lattice Estimator baseline run report must be private.")
    path = report_ref.get("path")
    if not isinstance(path, str) or not _is_private_report_path(path):
        failures.append(
            "Lattice Estimator baseline run report path must stay under private/."
        )


def _verify_contract_reference(
    report: dict[str, Any],
    root: Path,
    failures: list[str],
) -> list[dict[str, Any]]:
    contracts_ref = _dict_or_empty(report.get("contracts"))
    if (
        contracts_ref.get("schema_version")
        != LATTICE_ESTIMATOR_BASELINE_CONTRACTS_SCHEMA
    ):
        failures.append("Lattice Estimator baseline run contract schema drifted.")
    path_value = contracts_ref.get("path")
    sha_value = contracts_ref.get("sha256")
    if not isinstance(path_value, str):
        failures.append("Lattice Estimator baseline run contract path is invalid.")
        return []
    verification = verify_lattice_estimator_baseline_contracts(
        Path(path_value),
        root=root,
    )
    if not verification["accepted"]:
        failures.extend(
            f"Baseline contract verification failed: {failure}"
            for failure in verification["failures"]
        )
        return []
    contracts_path = _resolve_path(Path(path_value), root)
    if not isinstance(sha_value, str) or sha_value != _sha256_file(contracts_path):
        failures.append("Lattice Estimator baseline run contract digest drifted.")
    contracts = json.loads(contracts_path.read_text(encoding="utf-8"))
    entries = _contract_entries(contracts)
    if contracts_ref.get("contract_count") != len(entries):
        failures.append("Lattice Estimator baseline run contract count drifted.")
    return entries


def _verify_baseline_policy(report: dict[str, Any], failures: list[str]) -> None:
    policy = _dict_or_empty(report.get("baseline_policy"))
    expected = {
        "numeric_reference_outputs_committed": False,
        "private_numeric_outputs": True,
        "publication_allowed": False,
        "requires_expert_review_before_publication": True,
        "security_claim": False,
    }
    for key, expected_value in expected.items():
        if policy.get(key) != expected_value:
            if key == "publication_allowed":
                failures.append(
                    "Lattice Estimator baseline run must not allow publication."
                )
            else:
                failures.append(
                    f"Lattice Estimator baseline run baseline_policy {key} drifted."
                )


def _verify_safety(
    report: dict[str, Any],
    failures: list[str],
    summary: dict[str, Any],
) -> None:
    safety = _dict_or_empty(report.get("safety"))
    summary["lwe_only"] = safety.get("lwe_only")
    expected = {
        "arbitrary_candidate_code_execution": False,
        "external_network_access": False,
        "lwe_only": True,
        "numeric_reference_outputs_committed": False,
        "publishes_numeric_references": False,
        "raw_estimator_output_committed": False,
        "review_required_before_publication": True,
        "writes_only_allowed_private_roots": True,
    }
    for key, expected_value in expected.items():
        if safety.get(key) != expected_value:
            if key == "publishes_numeric_references":
                failures.append(
                    "Lattice Estimator baseline run must not publish numeric "
                    "references."
                )
            else:
                failures.append(f"Lattice Estimator baseline run safety {key} drifted.")


def _verify_results(
    report: dict[str, Any],
    expected_contracts: list[dict[str, Any]],
    failures: list[str],
) -> list[dict[str, Any]]:
    results = report.get("results")
    if not isinstance(results, list):
        failures.append("Lattice Estimator baseline run results must be a list.")
        return []
    typed_results: list[dict[str, Any]] = []
    if expected_contracts and len(results) != len(expected_contracts):
        failures.append("Lattice Estimator baseline run result count drifted.")
    for index, result in enumerate(results):
        if not isinstance(result, dict):
            failures.append(
                f"Lattice Estimator baseline run result {index} is invalid."
            )
            continue
        typed_results.append(result)
        expected = (
            expected_contracts[index] if index < len(expected_contracts) else None
        )
        _verify_result(index, result, expected, failures)
    return typed_results


def _verify_result(
    index: int,
    result: dict[str, Any],
    expected: dict[str, Any] | None,
    failures: list[str],
) -> None:
    if expected is not None:
        for field in (
            "attack_plan_id",
            "attack_type",
            "algorithm_key",
            "source_path",
            "target_family",
            "target_name",
        ):
            if result.get(field) != expected.get(field):
                failures.append(
                    f"Lattice Estimator baseline run result {index} {field} drifted."
                )
    if result.get("target_family") != "LWE":
        failures.append(f"Lattice Estimator baseline run result {index} is not LWE.")
    if result.get("evaluation_status") not in {"ok", "error", "unsupported"}:
        failures.append(
            f"Lattice Estimator baseline run result {index} status is invalid."
        )
    if result.get("evaluation_status") == "ok":
        if result.get("estimator_commit") != LATTICE_ESTIMATOR_PINNED_COMMIT:
            failures.append(
                f"Lattice Estimator baseline run result {index} is not pinned."
            )
        if result.get("commit_matches_pin") is not True:
            failures.append(
                f"Lattice Estimator baseline run result {index} pin flag drifted."
            )
    if result.get("public_reference_output") is not False:
        failures.append(
            "Lattice Estimator baseline run result "
            f"{index} has public reference output."
        )
    if "raw_output" in result:
        failures.append(
            f"Lattice Estimator baseline run result {index} exposed raw output."
        )
    if not _is_sha256(result.get("raw_output_sha256")):
        failures.append(
            f"Lattice Estimator baseline run result {index} raw digest is invalid."
        )
    _verify_numeric_result(index, result, failures)


def _verify_numeric_result(
    index: int,
    result: dict[str, Any],
    failures: list[str],
) -> None:
    has_numeric = (
        result.get("time_bits") is not None
        or result.get("memory_bits") is not None
    )
    if has_numeric and result.get("numeric_output_private") is not True:
        failures.append(
            "Lattice Estimator baseline run result "
            f"{index} numeric output is not private."
        )
    if result.get("numeric_output_private") is True:
        if not _is_number(result.get("time_bits")):
            failures.append(
                f"Lattice Estimator baseline run result {index} time_bits is invalid."
            )
        if not _is_number(result.get("memory_bits")):
            failures.append(
                f"Lattice Estimator baseline run result {index} memory_bits is invalid."
            )


def _verify_summary(
    report: dict[str, Any],
    results: list[dict[str, Any]],
    failures: list[str],
    verification_summary: dict[str, Any],
) -> None:
    summary = _dict_or_empty(report.get("summary"))
    expected = _summary(results)
    verification_summary.update(
        {
            "all_successful_results_from_pinned_commit": summary.get(
                "all_successful_results_from_pinned_commit"
            ),
            "contract_count": summary.get("contract_count"),
            "numeric_result_count": summary.get("numeric_result_count"),
            "ok_results": summary.get("ok_results"),
            "public_release_ok": summary.get("public_release_ok"),
            "raw_output_digest_count": sum(
                1 for result in results if _is_sha256(result.get("raw_output_sha256"))
            ),
            "security_claim": summary.get("security_claim"),
        }
    )
    for key, expected_value in expected.items():
        if summary.get(key) != expected_value:
            failures.append(f"Lattice Estimator baseline run summary {key} drifted.")
    if summary.get("public_release_ok") is not False:
        failures.append(
            "Lattice Estimator baseline run must not be public-release-ready."
        )
    if summary.get("security_claim") is not False:
        failures.append("Lattice Estimator baseline run must not claim security.")


def _verify_no_private_payload_leakage(
    report: dict[str, Any],
    failures: list[str],
) -> None:
    encoded = json.dumps(report, sort_keys=True)
    if '"raw_output":' in encoded:
        failures.append("Lattice Estimator baseline run exposed raw estimator output.")
    if '"attack_plan":' in encoded:
        failures.append("Lattice Estimator baseline run exposed AttackPlan payloads.")


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _is_private_report_path(path: str) -> bool:
    return PurePath(path).parts[:1] == ("private",)


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)
