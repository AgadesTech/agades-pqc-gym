from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path, PurePath
from typing import Any

from agades_pqc_gym.evaluators.lattice_estimator import (
    LATTICE_ESTIMATOR_PINNED_COMMIT,
)
from agades_pqc_gym.evolution.scheduler import validate_policy_private_path
from agades_pqc_gym.integrations.lattice_estimator_baseline_run import (
    LATTICE_ESTIMATOR_BASELINE_RUN_SCHEMA,
    verify_lattice_estimator_baseline_run,
)
from agades_pqc_gym.integrations.lattice_estimator_manifest import (
    LATTICE_ESTIMATOR_REPOSITORY,
)

LATTICE_ESTIMATOR_BASELINE_REVIEW_PACKET_SCHEMA = (
    "agades.pqc.lattice_estimator_baseline_review_packet.v1"
)
LATTICE_ESTIMATOR_BASELINE_REVIEW_PACKET_VERIFICATION_SCHEMA = (
    "agades.pqc.lattice_estimator_baseline_review_packet_verification.v1"
)
DEFAULT_BASELINE_REVIEW_PACKET_PATH = Path(
    "private/reports/lattice_estimator_baseline_review_packet.json"
)
FORBIDDEN_REVIEW_PACKET_KEYS = frozenset(
    {
        "attack_plan",
        "memory_bits",
        "raw_output",
        "time_bits",
    }
)
ALLOWED_RESULT_NUMERIC_FIELDS = frozenset({"warning_count"})


def build_lattice_estimator_baseline_review_packet(
    *,
    baseline_report_path: Path,
    contracts_root: Path | None = None,
    report_path: Path | None = None,
    reviewer_label: str = "pending-expert-review",
) -> dict[str, Any]:
    root = (contracts_root or Path.cwd()).resolve()
    baseline_verification = verify_lattice_estimator_baseline_run(
        baseline_report_path,
        contracts_root=root,
    )
    if not baseline_verification["accepted"]:
        failures = "; ".join(baseline_verification["failures"])
        raise ValueError(
            "Lattice Estimator baseline review packet requires a verified "
            f"private baseline report: {failures}"
        )
    baseline_report = _load_json_object(baseline_report_path)
    results = _result_evidence(baseline_report)
    summary = _summary(results, baseline_verification)

    return {
        "schema_version": LATTICE_ESTIMATOR_BASELINE_REVIEW_PACKET_SCHEMA,
        "created_at": "manual-baseline-review-packet-recorded",
        "report": {
            "path": (
                report_path or DEFAULT_BASELINE_REVIEW_PACKET_PATH
            ).as_posix(),
            "private": True,
        },
        "source_report": {
            "path": baseline_report_path.as_posix(),
            "schema_version": baseline_report["schema_version"],
            "sha256": _sha256_file(baseline_report_path),
        },
        "baseline_verification": {
            "accepted": baseline_verification["accepted"],
            "schema_version": baseline_verification["schema_version"],
            "summary": baseline_verification["summary"],
        },
        "upstream": {
            "repository": LATTICE_ESTIMATOR_REPOSITORY,
            "pinned_commit": LATTICE_ESTIMATOR_PINNED_COMMIT,
            "pin_source": "docs/lattice_estimator_manifest.json",
        },
        "review_status": {
            "state": "pending_expert_review",
            "reviewer_label": reviewer_label,
            "numeric_promotion_allowed": False,
            "public_claim_language_approved": False,
        },
        "summary": summary,
        "result_evidence": results,
        "review_questions": _review_questions(),
        "safety": {
            "contains_attack_plan_payloads": False,
            "contains_numeric_values": False,
            "contains_raw_estimator_output": False,
            "private_report": True,
            "publication_allowed": False,
            "public_release_ok": False,
            "requires_expert_review": True,
            "security_claim": False,
        },
    }


def write_lattice_estimator_baseline_review_packet(
    out: Path,
    *,
    baseline_report_path: Path,
    policy: dict[str, Any],
    contracts_root: Path | None = None,
    policy_root: Path | None = None,
    reviewer_label: str = "pending-expert-review",
) -> dict[str, Any]:
    output_root = (policy_root or Path.cwd()).resolve()
    validate_policy_private_path(out, policy=policy, root=output_root)
    packet = build_lattice_estimator_baseline_review_packet(
        baseline_report_path=baseline_report_path,
        contracts_root=contracts_root,
        report_path=out,
        reviewer_label=reviewer_label,
    )
    resolved_out = _resolve_path(out, output_root)
    resolved_out.parent.mkdir(parents=True, exist_ok=True)
    resolved_out.write_text(
        json.dumps(packet, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return packet


def verify_lattice_estimator_baseline_review_packet(
    packet_path: Path,
    *,
    baseline_report_path: Path | None = None,
    contracts_root: Path | None = None,
) -> dict[str, Any]:
    root = (contracts_root or Path.cwd()).resolve()
    failures: list[str] = []
    packet = _load_packet(packet_path, failures)
    summary = {
        "baseline_verification_accepted": False,
        "contains_numeric_values": None,
        "failure_count": 0,
        "private_report": None,
        "raw_output_digest_count": 0,
        "result_count": 0,
        "security_claim": None,
    }

    if packet is not None:
        _verify_packet_schema(packet, failures)
        _verify_packet_report(packet, failures, summary)
        resolved_baseline = _baseline_report_path(
            packet,
            baseline_report_path=baseline_report_path,
        )
        _verify_source_report(packet, resolved_baseline, root, failures, summary)
        _verify_packet_summary(packet, failures, summary)
        _verify_result_evidence(packet, failures, summary)
        _verify_review_status(packet, failures)
        _verify_packet_safety(packet, failures, summary)
        _verify_no_forbidden_payload_keys(packet, failures)

    summary["failure_count"] = len(failures)
    return {
        "schema_version": LATTICE_ESTIMATOR_BASELINE_REVIEW_PACKET_VERIFICATION_SCHEMA,
        "packet_path": packet_path.as_posix(),
        "accepted": not failures,
        "summary": summary,
        "failures": failures,
    }


def _result_evidence(baseline_report: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = []
    for result in baseline_report["results"]:
        evidence.append(
            {
                "algorithm_key": result["algorithm_key"],
                "attack_plan_id": result["attack_plan_id"],
                "attack_type": result["attack_type"],
                "commit_matches_pin": result["commit_matches_pin"],
                "estimator_commit": result["estimator_commit"],
                "estimator_name": result["estimator_name"],
                "estimator_version": result["estimator_version"],
                "evaluation_status": result["evaluation_status"],
                "numeric_output_private": result["numeric_output_private"],
                "public_reference_output": result["public_reference_output"],
                "raw_output_sha256": result["raw_output_sha256"],
                "source_path": result["source_path"],
                "target_family": result["target_family"],
                "target_name": result["target_name"],
                "warning_count": len(result.get("warnings", [])),
            }
        )
    return evidence


def _summary(
    results: list[dict[str, Any]],
    baseline_verification: dict[str, Any],
) -> dict[str, Any]:
    baseline_summary = baseline_verification["summary"]
    return {
        "algorithm_keys": [result["algorithm_key"] for result in results],
        "contract_count": baseline_summary["contract_count"],
        "numeric_result_count": baseline_summary["numeric_result_count"],
        "raw_output_digest_count": baseline_summary["raw_output_digest_count"],
        "result_count": len(results),
        "review_question_count": len(_review_questions()),
    }


def _review_questions() -> list[str]:
    return [
        "Confirm each public toy AttackPlan maps to the intended LWE estimator call.",
        "Review target parameters, secret/error distributions, and sample counts.",
        "Inspect private numeric outputs locally before any public promotion.",
        "Approve or reject each raw-output digest as reproducible evidence.",
        "Approve public claim language separately from numeric reproducibility.",
    ]


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}.")
    return payload


def _load_packet(path: Path, failures: list[str]) -> dict[str, Any] | None:
    if not path.exists():
        failures.append(f"Lattice Estimator baseline review packet is missing: {path}.")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(
            "Lattice Estimator baseline review packet is invalid JSON at line "
            f"{exc.lineno}: {exc.msg}."
        )
        return None
    if not isinstance(payload, dict):
        failures.append(
            "Lattice Estimator baseline review packet must be a JSON object."
        )
        return None
    return payload


def _verify_packet_schema(packet: dict[str, Any], failures: list[str]) -> None:
    if packet.get("schema_version") != LATTICE_ESTIMATOR_BASELINE_REVIEW_PACKET_SCHEMA:
        failures.append("Lattice Estimator baseline review packet schema drifted.")


def _verify_packet_report(
    packet: dict[str, Any],
    failures: list[str],
    summary: dict[str, Any],
) -> None:
    report = _dict_or_empty(packet.get("report"))
    summary["private_report"] = report.get("private")
    if report.get("private") is not True:
        failures.append("Lattice Estimator baseline review packet must be private.")
    path = report.get("path")
    if not isinstance(path, str) or not _is_private_path(path):
        failures.append(
            "Lattice Estimator baseline review packet path must stay under private/."
        )


def _verify_source_report(
    packet: dict[str, Any],
    baseline_path: Path,
    root: Path,
    failures: list[str],
    summary: dict[str, Any],
) -> None:
    source = _dict_or_empty(packet.get("source_report"))
    if source.get("schema_version") != LATTICE_ESTIMATOR_BASELINE_RUN_SCHEMA:
        failures.append(
            "Lattice Estimator baseline review packet source schema drifted."
        )
    if not baseline_path.exists():
        failures.append(
            "Baseline report referenced by review packet is missing: "
            f"{baseline_path}."
        )
        return
    if source.get("sha256") != _sha256_file(baseline_path):
        failures.append(
            "Lattice Estimator baseline review packet source digest drifted."
        )
    verification = verify_lattice_estimator_baseline_run(
        baseline_path,
        contracts_root=root,
    )
    summary["baseline_verification_accepted"] = verification["accepted"]
    if not verification["accepted"]:
        failures.extend(
            f"Review packet baseline verification failed: {failure}"
            for failure in verification["failures"]
        )
    stored = _dict_or_empty(packet.get("baseline_verification"))
    if stored.get("accepted") is not True:
        failures.append(
            "Lattice Estimator baseline review packet lacks accepted verification."
        )
    if stored.get("summary") != verification["summary"]:
        failures.append(
            "Lattice Estimator baseline review packet verification summary drifted."
        )


def _verify_packet_summary(
    packet: dict[str, Any],
    failures: list[str],
    verification_summary: dict[str, Any],
) -> None:
    summary = _dict_or_empty(packet.get("summary"))
    results = packet.get("result_evidence")
    if not isinstance(results, list):
        failures.append("Lattice Estimator baseline review packet evidence is invalid.")
        results = []
    expected = {
        "algorithm_keys": [
            result.get("algorithm_key")
            for result in results
            if isinstance(result, dict)
        ],
        "contract_count": len(results),
        "numeric_result_count": sum(
            1
            for result in results
            if isinstance(result, dict)
            and result.get("numeric_output_private") is True
        ),
        "raw_output_digest_count": sum(
            1
            for result in results
            if isinstance(result, dict) and _is_sha256(result.get("raw_output_sha256"))
        ),
        "result_count": len(results),
        "review_question_count": len(_review_questions()),
    }
    for key, expected_value in expected.items():
        if summary.get(key) != expected_value:
            failures.append(
                f"Lattice Estimator baseline review packet summary {key} drifted."
            )
    verification_summary["raw_output_digest_count"] = expected[
        "raw_output_digest_count"
    ]
    verification_summary["result_count"] = expected["result_count"]


def _verify_result_evidence(
    packet: dict[str, Any],
    failures: list[str],
    summary: dict[str, Any],
) -> None:
    evidence = packet.get("result_evidence")
    if not isinstance(evidence, list):
        return
    for index, entry in enumerate(evidence):
        if not isinstance(entry, dict):
            failures.append(
                f"Lattice Estimator baseline review packet evidence {index} is invalid."
            )
            continue
        for forbidden in FORBIDDEN_REVIEW_PACKET_KEYS:
            if forbidden in entry:
                failures.append(
                    "Lattice Estimator baseline review packet contains "
                    f"numeric field or private payload key: {forbidden}."
                )
        if entry.get("target_family") != "LWE":
            failures.append(
                f"Lattice Estimator baseline review packet evidence {index} is not LWE."
            )
        if entry.get("estimator_commit") != LATTICE_ESTIMATOR_PINNED_COMMIT:
            failures.append(
                "Lattice Estimator baseline review packet evidence "
                f"{index} is unpinned."
            )
        if entry.get("commit_matches_pin") is not True:
            failures.append(
                "Lattice Estimator baseline review packet evidence "
                f"{index} pin flag drifted."
            )
        if entry.get("public_reference_output") is not False:
            failures.append(
                "Lattice Estimator baseline review packet evidence "
                f"{index} has public reference output."
            )
        if not _is_sha256(entry.get("raw_output_sha256")):
            failures.append(
                "Lattice Estimator baseline review packet evidence "
                f"{index} raw digest is invalid."
            )
    summary["contains_numeric_values"] = _contains_forbidden_evidence(packet)


def _verify_review_status(packet: dict[str, Any], failures: list[str]) -> None:
    status = _dict_or_empty(packet.get("review_status"))
    expected = {
        "state": "pending_expert_review",
        "numeric_promotion_allowed": False,
        "public_claim_language_approved": False,
    }
    for key, expected_value in expected.items():
        if status.get(key) != expected_value:
            failures.append(
                f"Lattice Estimator baseline review packet review_status {key} drifted."
            )
    if (
        not isinstance(status.get("reviewer_label"), str)
        or not status["reviewer_label"]
    ):
        failures.append(
            "Lattice Estimator baseline review packet reviewer label is invalid."
        )


def _verify_packet_safety(
    packet: dict[str, Any],
    failures: list[str],
    summary: dict[str, Any],
) -> None:
    safety = _dict_or_empty(packet.get("safety"))
    summary["security_claim"] = safety.get("security_claim")
    expected = {
        "contains_attack_plan_payloads": False,
        "contains_numeric_values": False,
        "contains_raw_estimator_output": False,
        "private_report": True,
        "publication_allowed": False,
        "public_release_ok": False,
        "requires_expert_review": True,
        "security_claim": False,
    }
    for key, expected_value in expected.items():
        if safety.get(key) != expected_value:
            failures.append(
                f"Lattice Estimator baseline review packet safety {key} drifted."
            )


def _verify_no_forbidden_payload_keys(
    packet: dict[str, Any],
    failures: list[str],
) -> None:
    forbidden = _forbidden_keys(packet)
    forbidden_numeric = _forbidden_result_numeric_fields(packet)
    forbidden_items = forbidden | forbidden_numeric
    if forbidden_items:
        joined = ", ".join(sorted(forbidden_items))
        failures.append(
            "Lattice Estimator baseline review packet contains numeric field "
            f"or private payload key: {joined}."
        )


def _baseline_report_path(
    packet: dict[str, Any],
    *,
    baseline_report_path: Path | None,
) -> Path:
    if baseline_report_path is not None:
        return baseline_report_path
    source = _dict_or_empty(packet.get("source_report"))
    path = source.get("path")
    return Path(path) if isinstance(path, str) else Path("__missing_baseline_report__")


def _forbidden_keys(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN_REVIEW_PACKET_KEYS:
                found.add(key)
            found.update(_forbidden_keys(item))
    elif isinstance(value, list):
        for item in value:
            found.update(_forbidden_keys(item))
    return found


def _forbidden_result_numeric_fields(packet: dict[str, Any]) -> set[str]:
    evidence = packet.get("result_evidence")
    if not isinstance(evidence, list):
        return set()
    found: set[str] = set()
    for index, entry in enumerate(evidence):
        if not isinstance(entry, dict):
            continue
        found.update(
            f"result_evidence[{index}].{field}"
            for field in _numeric_fields(entry)
            if field not in ALLOWED_RESULT_NUMERIC_FIELDS
        )
    return found


def _numeric_fields(value: Any, prefix: str = "") -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            found.update(_numeric_fields(item, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            path = f"{prefix}[{index}]"
            found.update(_numeric_fields(item, path))
    elif isinstance(value, int | float) and not isinstance(value, bool):
        found.add(prefix)
    return found


def _contains_forbidden_evidence(value: dict[str, Any]) -> bool:
    return bool(_forbidden_keys(value) or _forbidden_result_numeric_fields(value))


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _resolve_path(path: Path, root: Path) -> Path:
    return path if path.is_absolute() else root / path


def _is_private_path(path: str) -> bool:
    return PurePath(path).parts[:1] == ("private",)


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()
