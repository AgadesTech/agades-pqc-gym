from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.evaluators.lattice_estimator import (
    LATTICE_ESTIMATOR_PINNED_COMMIT,
    reviewed_lwe_estimator_mappings,
)
from agades_pqc_gym.evaluators.lattice_estimator_checkout import (
    LATTICE_ESTIMATOR_REPOSITORY,
)

LATTICE_ESTIMATOR_MANIFEST_SCHEMA = "agades.pqc.lattice_estimator_manifest.v1"
LATTICE_ESTIMATOR_MANIFEST_VERIFICATION_SCHEMA = (
    "agades.pqc.lattice_estimator_manifest_verification.v1"
)
LATTICE_ESTIMATOR_OBSERVED_AT = "2026-05-16"
ROOT = Path(__file__).resolve().parents[3]
_EXPECTED_PROJECT = {
    "name": "Agades PQC Gym",
    "repository": "https://github.com/AgadesTech/agades-pqc-gym",
    "package": "agades_pqc_gym",
    "cli": "agades-pqc",
}
_EXPECTED_PIN_ENFORCEMENT = {
    "runtime_required_commit": LATTICE_ESTIMATOR_PINNED_COMMIT,
    "missing_commit_metadata": "error",
    "mismatched_commit": "error",
}
_EXPECTED_SOURCE_CHECKOUT_BACKEND = {
    "cli_option": "--estimator-source",
    "clean_tree_probe": "git status --porcelain",
    "clean_tree_verified_before_import": True,
    "commit_probe": "git rev-parse HEAD",
    "commit_verified_before_import": True,
    "dirty_checkout": "error_before_import",
    "entrypoint_verified_before_import": True,
    "mismatched_checkout_commit": "error_before_import",
    "mismatched_origin": "error_before_import",
    "origin_probe": "git remote get-url origin",
    "origin_verified_before_import": True,
    "scope": "private_lattice_estimator_baseline_runs",
}
_EXPECTED_RUNTIME_ENVIRONMENT = {
    "ci_dependency": False,
    "missing_runtime_behavior": "private_error_report_without_public_numeric_outputs",
    "private_preflight_command": (
        "uv run agades-pqc lattice-estimator-runtime-preflight "
        "--out private/reports/lattice_estimator_runtime_preflight.json "
        "--policy docs/private_run_policy.json"
    ),
    "private_preflight_verify_command": (
        "uv run agades-pqc lattice-estimator-runtime-preflight-verify "
        "--preflight private/reports/lattice_estimator_runtime_preflight.json"
    ),
    "private_baseline_sage_worker_command": (
        "uv run agades-pqc lattice-estimator-baseline-run "
        "--contracts docs/lattice_estimator_baseline_contracts.json "
        "--contracts-root . "
        "--out private/reports/lattice_estimator_baseline_run.json "
        "--policy docs/private_run_policy.json "
        "--estimator-source /path/to/lattice-estimator "
        "--sage-command sage"
    ),
    "private_baseline_sage_python_worker_command": (
        "uv run agades-pqc lattice-estimator-baseline-run "
        "--contracts docs/lattice_estimator_baseline_contracts.json "
        "--contracts-root . "
        "--out private/reports/lattice_estimator_baseline_run.json "
        "--policy docs/private_run_policy.json "
        "--estimator-source /path/to/lattice-estimator "
        "--sage-python-command '/path/to/python-with-sage-all'"
    ),
    "private_baseline_verify_command": (
        "uv run agades-pqc lattice-estimator-baseline-run-verify "
        "--report private/reports/lattice_estimator_baseline_run.json "
        "--contracts-root ."
    ),
    "private_baseline_review_packet_command": (
        "uv run agades-pqc lattice-estimator-baseline-review-packet "
        "--baseline-report private/reports/lattice_estimator_baseline_run.json "
        "--out private/reports/lattice_estimator_baseline_review_packet.json "
        "--policy docs/private_run_policy.json "
        "--contracts-root ."
    ),
    "private_baseline_review_packet_verify_command": (
        "uv run agades-pqc lattice-estimator-baseline-review-packet-verify "
        "--packet private/reports/lattice_estimator_baseline_review_packet.json "
        "--baseline-report private/reports/lattice_estimator_baseline_run.json "
        "--contracts-root ."
    ),
    "required_for_numeric_baseline": True,
    "sage_command": "sage",
    "sage_python_command_default": "sage -python",
    "sage_python_command_option": "--sage-python-command",
    "sage_python_probe": "<sage-python-command> -c 'import sage.all'",
    "sage_worker": "private_subprocess_after_checkout_preflight",
}
_REQUIRED_RELEASE_GATES = (
    "uv run pytest tests/test_lattice_estimator_manifest.py -q",
    "uv run agades-pqc lattice-estimator-manifest --out "
    "docs/lattice_estimator_manifest.json",
    "uv run agades-pqc lattice-estimator-manifest-verify --manifest "
    "docs/lattice_estimator_manifest.json",
    "uv run agades-pqc family-support-verify --matrix "
    "docs/family_support_matrix.json",
    "uv run agades-pqc family-operator-catalog-verify --catalog "
    "docs/family_operator_catalog.json",
    "uv run agades-pqc ecosystem-smoke-verify --report "
    "reports/ecosystem_smoke.json",
    "uv run agades-pqc release-audit --out public/release_audit.json",
)
_EXPECTED_FALSE_SAFETY_FLAGS = (
    "arbitrary_code_execution",
    "live_targeting",
    "security_claim",
    "use_for_public_security_claims",
)


def build_lattice_estimator_manifest() -> dict[str, Any]:
    return {
        "schema_version": LATTICE_ESTIMATOR_MANIFEST_SCHEMA,
        "project": {
            **_EXPECTED_PROJECT,
        },
        "upstream": {
            "repository": LATTICE_ESTIMATOR_REPOSITORY,
            "branch": "main",
            "observed_ref": "refs/heads/main",
            "pinned_commit": LATTICE_ESTIMATOR_PINNED_COMMIT,
            "pinned_commit_url": (
                f"{LATTICE_ESTIMATOR_REPOSITORY}/commit/"
                f"{LATTICE_ESTIMATOR_PINNED_COMMIT}"
            ),
            "observed_at": LATTICE_ESTIMATOR_OBSERVED_AT,
        },
        "agades_boundary": {
            "adapter_module": "agades_pqc_gym.evaluators.lattice_estimator",
            "optional_import": "estimator",
            "enabled_target_families": ["LWE"],
            "mlwe_status": "warning_gated_flattening",
            "schema_only_lattice_families": ["NTRU", "SIS"],
            "reviewed_lwe_mappings": reviewed_lwe_estimator_mappings(),
            "unsupported_behavior": "return_structured_unsupported_or_error_result",
            "pin_enforcement": {**_EXPECTED_PIN_ENFORCEMENT},
            "source_checkout_backend": {**_EXPECTED_SOURCE_CHECKOUT_BACKEND},
            "runtime_environment": {**_EXPECTED_RUNTIME_ENVIRONMENT},
        },
        "safety": {
            "arbitrary_code_execution": False,
            "live_targeting": False,
            "security_claim": False,
            "use_for_public_security_claims": False,
            "review_required_before_security_claims": True,
        },
        "release": {
            "generator_command": (
                "uv run agades-pqc lattice-estimator-manifest --out "
                "docs/lattice_estimator_manifest.json"
            ),
            "audit_gate": "lattice-estimator-pin",
            "review_required_before_publish": True,
        },
        "release_gates": [
            *_REQUIRED_RELEASE_GATES,
        ],
    }


def write_lattice_estimator_manifest(out: Path) -> dict[str, Any]:
    manifest = build_lattice_estimator_manifest()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def verify_lattice_estimator_manifest(
    manifest_path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    manifest = _read_lattice_estimator_manifest(
        manifest_path,
        project_root,
        failures,
    )
    expected = build_lattice_estimator_manifest()

    if manifest != expected:
        failures.append("Lattice Estimator manifest is not in sync.")

    _verify_project_metadata(manifest, failures)
    _verify_upstream(manifest, failures)
    _verify_boundary(manifest, failures)
    _verify_safety(manifest, failures)
    _verify_release(manifest, failures)
    _verify_release_gates(manifest, failures)

    return _verification_result(manifest_path, manifest, failures)


def _read_lattice_estimator_manifest(
    manifest_path: Path,
    root: Path,
    failures: list[str],
) -> dict[str, Any]:
    path = manifest_path if manifest_path.is_absolute() else root / manifest_path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"Lattice Estimator manifest is missing: {manifest_path}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(
            f"Lattice Estimator manifest is invalid JSON at line {exc.lineno}."
        )
        return {}

    if not isinstance(payload, dict):
        failures.append("Lattice Estimator manifest must be a JSON object.")
        return {}
    return payload


def _verify_project_metadata(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    if manifest.get("schema_version") != LATTICE_ESTIMATOR_MANIFEST_SCHEMA:
        failures.append(
            "Lattice Estimator manifest schema_version must be "
            f"{LATTICE_ESTIMATOR_MANIFEST_SCHEMA}."
        )
    project = manifest.get("project")
    if not isinstance(project, dict):
        failures.append("Lattice Estimator manifest project must be an object.")
        return
    for key, expected in _EXPECTED_PROJECT.items():
        if project.get(key) != expected:
            failures.append(f"Lattice Estimator manifest project.{key} drifted.")


def _verify_upstream(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    upstream = manifest.get("upstream")
    if not isinstance(upstream, dict):
        failures.append("Lattice Estimator manifest upstream must be an object.")
        return

    pinned_commit = upstream.get("pinned_commit")
    if pinned_commit != LATTICE_ESTIMATOR_PINNED_COMMIT:
        failures.append("Lattice Estimator pinned commit differs from generator.")
    if not isinstance(pinned_commit, str) or len(pinned_commit) != 40:
        failures.append("Lattice Estimator pinned commit must be a full SHA-1.")
    if upstream.get("repository") != LATTICE_ESTIMATOR_REPOSITORY:
        failures.append("Lattice Estimator upstream repository is unexpected.")
    if upstream.get("branch") != "main":
        failures.append("Lattice Estimator upstream branch is unexpected.")
    if upstream.get("observed_ref") != "refs/heads/main":
        failures.append("Lattice Estimator observed ref is unexpected.")
    expected_commit_url = (
        f"{LATTICE_ESTIMATOR_REPOSITORY}/commit/{LATTICE_ESTIMATOR_PINNED_COMMIT}"
    )
    if upstream.get("pinned_commit_url") != expected_commit_url:
        failures.append("Lattice Estimator pinned commit URL drifted.")
    if upstream.get("observed_at") != LATTICE_ESTIMATOR_OBSERVED_AT:
        failures.append("Lattice Estimator observation date drifted.")


def _verify_boundary(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    boundary = manifest.get("agades_boundary")
    if not isinstance(boundary, dict):
        failures.append(
            "Lattice Estimator manifest agades_boundary must be an object."
        )
        return

    if boundary.get("adapter_module") != "agades_pqc_gym.evaluators.lattice_estimator":
        failures.append("Lattice Estimator adapter module drifted.")
    if boundary.get("optional_import") != "estimator":
        failures.append("Lattice Estimator optional import marker drifted.")
    if boundary.get("enabled_target_families") != ["LWE"]:
        failures.append("Lattice Estimator manifest must stay LWE-only.")
    if boundary.get("mlwe_status") != "warning_gated_flattening":
        failures.append("Lattice Estimator MLWE status drifted.")
    if boundary.get("schema_only_lattice_families") != ["NTRU", "SIS"]:
        failures.append("Lattice Estimator manifest must keep NTRU/SIS schema-only.")
    if boundary.get("reviewed_lwe_mappings") != reviewed_lwe_estimator_mappings():
        failures.append("Lattice Estimator reviewed mapping set is out of sync.")
    if (
        boundary.get("unsupported_behavior")
        != "return_structured_unsupported_or_error_result"
    ):
        failures.append("Lattice Estimator unsupported behavior drifted.")
    if boundary.get("pin_enforcement") != _EXPECTED_PIN_ENFORCEMENT:
        failures.append(
            "Lattice Estimator manifest must record runtime pin enforcement."
        )
    if boundary.get("source_checkout_backend") != _EXPECTED_SOURCE_CHECKOUT_BACKEND:
        failures.append(
            "Lattice Estimator local checkout backend must verify checkout "
            "readiness before import."
        )
    if boundary.get("runtime_environment") != _EXPECTED_RUNTIME_ENVIRONMENT:
        failures.append(
            "Lattice Estimator manifest must document the Sage runtime preflight."
        )


def _verify_safety(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    safety = manifest.get("safety")
    if not isinstance(safety, dict):
        failures.append("Lattice Estimator manifest safety must be an object.")
        return
    for flag in _EXPECTED_FALSE_SAFETY_FLAGS:
        if safety.get(flag) is not False:
            if flag == "security_claim":
                failures.append(
                    "Lattice Estimator manifest advertises a security claim."
                )
            elif flag == "use_for_public_security_claims":
                failures.append(
                    "Lattice Estimator manifest permits public security claims."
                )
            else:
                failures.append(f"Lattice Estimator safety.{flag} must be false.")
    if safety.get("review_required_before_security_claims") is not True:
        failures.append("Lattice Estimator manifest lacks review-before-claim gate.")


def _verify_release(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    release = manifest.get("release")
    if not isinstance(release, dict):
        failures.append("Lattice Estimator manifest release must be an object.")
        return
    if release.get("generator_command") != _REQUIRED_RELEASE_GATES[1]:
        failures.append("Lattice Estimator generator command drifted.")
    if release.get("audit_gate") != "lattice-estimator-pin":
        failures.append("Lattice Estimator audit gate drifted.")
    if release.get("review_required_before_publish") is not True:
        failures.append("Lattice Estimator release lacks review gate.")


def _verify_release_gates(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    release_gates = manifest.get("release_gates")
    if not isinstance(release_gates, list):
        failures.append("Lattice Estimator release_gates must be a list.")
        return
    for required_gate in _REQUIRED_RELEASE_GATES:
        if required_gate not in release_gates:
            failures.append(
                f"Lattice Estimator release gate missing: {required_gate}"
            )


def _verification_result(
    manifest_path: Path,
    manifest: dict[str, Any],
    failures: list[str],
) -> dict[str, Any]:
    boundary = manifest.get("agades_boundary", {})
    if not isinstance(boundary, dict):
        boundary = {}
    upstream = manifest.get("upstream", {})
    if not isinstance(upstream, dict):
        upstream = {}
    safety = manifest.get("safety", {})
    if not isinstance(safety, dict):
        safety = {}
    mappings = boundary.get("reviewed_lwe_mappings", {})
    if not isinstance(mappings, dict):
        mappings = {}
    expected_mappings = reviewed_lwe_estimator_mappings()
    covered_mappings = sorted(
        [
            (attack_type, algorithm_key)
            for attack_type, algorithm_key in expected_mappings.items()
            if mappings.get(attack_type) == algorithm_key
        ],
        key=lambda item: item[1],
    )
    covered_attack_types = [attack_type for attack_type, _ in covered_mappings]
    covered_algorithm_keys = [algorithm_key for _, algorithm_key in covered_mappings]
    release_gates = manifest.get("release_gates", [])
    if not isinstance(release_gates, list):
        release_gates = []

    return {
        "schema_version": LATTICE_ESTIMATOR_MANIFEST_VERIFICATION_SCHEMA,
        "manifest_path": manifest_path.as_posix(),
        "accepted": not failures,
        "summary": {
            "covered_algorithm_keys": covered_algorithm_keys,
            "covered_attack_types": covered_attack_types,
            "failure_count": len(failures),
            "mapping_count": len(mappings),
            "pinned_commit": upstream.get("pinned_commit"),
            "release_gate_count": len(release_gates),
            "schema_only_lattice_families": boundary.get(
                "schema_only_lattice_families"
            ),
            "security_claim": safety.get("security_claim"),
            "runtime_environment": boundary.get("runtime_environment")
            == _EXPECTED_RUNTIME_ENVIRONMENT,
            "source_checkout_backend": boundary.get("source_checkout_backend")
            == _EXPECTED_SOURCE_CHECKOUT_BACKEND,
        },
        "failures": failures,
    }
