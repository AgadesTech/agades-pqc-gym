from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.core.target import TargetFamily
from agades_pqc_gym.formal.artifacts import MVP_VERTICAL_PROOF_ARTIFACT_PATHS
from agades_pqc_gym.formal.review import (
    FAMILY_REVIEWER_ROLE_IDS,
    REVIEW_STATUSES,
    REVIEWER_ROLE_GROUPS,
    required_reviewers_for_family,
)

REVIEWER_GOVERNANCE_SCHEMA = "agades.pqc.reviewer_governance.v1"
REVIEWER_GOVERNANCE_VERIFICATION_SCHEMA = (
    "agades.pqc.reviewer_governance_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_GOVERNANCE_PATH = Path("docs/reviewer_governance.json")
FAMILY_REVIEW_COMPETENCIES = {
    TargetFamily.LWE.value: [
        "LWE/BDD/SIS reductions and lattice attack applicability",
        "Lattice Estimator assumptions and cost-model boundaries",
    ],
    TargetFamily.MLWE.value: [
        "module lattice assumptions and parameter shape",
        "MLWE-to-LWE modelling limits and estimator caveats",
    ],
    TargetFamily.NTRU.value: [
        "NTRU target shape and secret/error distribution constraints",
        "schema-only placeholder boundary review",
    ],
    TargetFamily.SIS.value: [
        "SIS target shape and norm-bound constraints",
        "schema-only placeholder boundary review",
    ],
    TargetFamily.CODE_BASED.value: [
        "syndrome decoding and code parameter invariants",
        "information-set-decoding toy-vs-real boundary",
    ],
    TargetFamily.MULTIVARIATE.value: [
        "MQ/minrank/UOV parameter invariants",
        "finite-field and equation/variable applicability",
    ],
    TargetFamily.HASH_BASED.value: [
        "hash/preimage/collision/security-bound semantics",
        "signature/authentication-path misuse boundaries",
    ],
    TargetFamily.ISOGENY_HISTORICAL.value: [
        "historical isogeny attack scope",
        "non-current-claim and educational-fixture boundary",
    ],
    TargetFamily.IMPLEMENTATION_SECURITY.value: [
        "side-channel/KAT/benchmark review scope",
        "no conformance or production-security claim boundary",
    ],
}
LINKED_ARTIFACT_PATHS = {
    "formal_estimator_model": "docs/formal_estimator_model.json",
    "formal_family_coverage": "docs/formal_family_coverage.json",
    "formal_operator_semantics": "docs/formal_operator_semantics.json",
    "formal_lean_backend": "docs/formal_lean_backend.json",
    "formal_lwe_proof_artifact": MVP_VERTICAL_PROOF_ARTIFACT_PATHS[
        TargetFamily.LWE.value
    ],
    "formal_mlwe_proof_artifact": MVP_VERTICAL_PROOF_ARTIFACT_PATHS[
        TargetFamily.MLWE.value
    ],
    "private_run_policy": "docs/private_run_policy.json",
    "private_training_manifest": "docs/private_training_config_manifest.json",
    "external_publication_review_packet": (
        "docs/external_publication_review_packet.json"
    ),
    "publication_manifest": "docs/publication_manifest.json",
    "release_audit": "public/release_audit.json",
}


def build_reviewer_governance(root: Path | None = None) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    return {
        "schema_version": REVIEWER_GOVERNANCE_SCHEMA,
        "project": {
            "name": "Agades PQC Gym",
            "repository": "https://github.com/AgadesTech/agades-pqc-gym",
            "package": "agades_pqc_gym",
        },
        "role_groups": {
            "family_cryptography_reviewer": {
                "minimum_reviewers_per_family_artifact": 1,
                "role_ids": sorted(set(FAMILY_REVIEWER_ROLE_IDS.values())),
                "assignment_status": "role_required_unassigned",
            },
            "formal_methods_reviewer": {
                "minimum_reviewers": 1,
                "required_expertise": [
                    "Lean 4 theorem and source binding review",
                    "Mathlib-backed proof obligation typing",
                    "artifact hash and source-path binding review",
                    "SMT/Z3 finite-obligation audit when used",
                ],
            },
            "release_boundary_reviewer": {
                "minimum_reviewers": 1,
                "required_expertise": [
                    "OSS redaction and no-secret publication review",
                    "no-public-PQC-break-claim review",
                    "private dataset/model/trace holdback review",
                    "Hugging Face, Prime Intellect, and NVIDIA metadata review",
                ],
            },
        },
        "family_reviewers": _family_reviewers(),
        "formal_backend_policy": {
            "primary": {
                "backend": "lean4",
                "library": "mathlib",
                "required_for_security_claims": True,
            },
            "smt_assist": {
                "backend": "z3",
                "scope": "optional_finite_decidable_obligations_only",
                "may_replace_primary_backend": False,
            },
        },
        "approval_gates": _approval_gates(),
        "review_artifact_format": {
            "schema_version": "agades.pqc.review_artifact.v1",
            "status_field": "review.status",
            "supported_statuses": list(REVIEW_STATUSES),
            "required_fields": [
                "artifact_path",
                "artifact_sha256",
                "target_family",
                "review.status",
                "review.required_reviewers",
                "review.claim_boundary",
            ],
            "status_before_domain_claim": "reviewed",
            "unassigned_role_status": "role_required_unassigned",
        },
        "formal_artifact_binding": {
            "formal_estimator_model_path": "docs/formal_estimator_model.json",
            "formal_family_coverage_path": "docs/formal_family_coverage.json",
            "formal_operator_semantics_path": (
                "docs/formal_operator_semantics.json"
            ),
            "mvp_vertical_proof_artifacts": dict(MVP_VERTICAL_PROOF_ARTIFACT_PATHS),
            "required_reviewers_by_family": _required_reviewers_by_family(),
            "claim_boundary_contains": "not PQC break claims",
        },
        "private_training_review": {
            "sources": [
                "facebookresearch/LWE-benchmarking",
                "facebook/TAPAS",
                "pq-code-package",
            ],
            "required_controls": [
                "license_review",
                "provenance_tracking",
                "deduplication",
                "redaction",
                "contamination_audit",
            ],
            "publication_allowed": False,
            "train_traces_publication_allowed": False,
            "reviewer_annotations_publication_allowed": False,
            "finetuned_qwen_publication_allowed": False,
        },
        "rl_environment_contract_path": "docs/rl_environment_contract.json",
        "linked_artifacts": _linked_artifacts(project_root),
        "release_gates": [
            "uv run pytest tests/test_reviewer_governance.py -q",
            "uv run agades-pqc reviewer-governance --out "
            "docs/reviewer_governance.json",
            "uv run agades-pqc reviewer-governance-verify --governance "
            "docs/reviewer_governance.json",
        ],
    }


def write_reviewer_governance(
    out: Path = DEFAULT_GOVERNANCE_PATH,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    governance = build_reviewer_governance(root=root)
    resolved = _resolve_path(out, (root or ROOT).resolve())
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        json.dumps(governance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return governance


def verify_reviewer_governance(
    governance_path: Path = DEFAULT_GOVERNANCE_PATH,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    governance = _read_json_object(
        _resolve_path(governance_path, project_root),
        "Reviewer governance",
        failures,
    )
    expected = build_reviewer_governance(root=project_root)

    if governance and governance != expected:
        failures.append("Reviewer governance is not in sync.")
    if governance:
        _verify_schema(governance, failures)
        _verify_role_groups(governance, failures)
        _verify_family_reviewers(governance, failures)
        _verify_formal_backend_policy(governance, failures)
        _verify_approval_gates(governance, failures)
        _verify_private_training_review(governance, failures)
        _verify_formal_artifact_binding(governance, project_root, failures)
        _verify_linked_artifacts(governance, expected, project_root, failures)

    summary = {
        "family_reviewers": len(governance.get("family_reviewers", [])),
        "role_groups": len(governance.get("role_groups", {})),
        "approval_gates": len(governance.get("approval_gates", {})),
        "linked_artifacts": len(governance.get("linked_artifacts", {})),
        "failure_count": len(failures),
    }
    return {
        "schema_version": REVIEWER_GOVERNANCE_VERIFICATION_SCHEMA,
        "governance_path": governance_path.as_posix(),
        "accepted": not failures,
        "summary": summary,
        "failures": failures,
    }


def _family_reviewers() -> list[dict[str, Any]]:
    return [
        {
            "family": family.value,
            "role_group": "family_cryptography_reviewer",
            "role_id": FAMILY_REVIEWER_ROLE_IDS[family.value],
            "minimum_reviewers": 1,
            "assignment_status": "role_required_unassigned",
            "required_expertise": list(FAMILY_REVIEW_COMPETENCIES[family.value]),
            "required_before_security_claim": True,
            "required_before_family_release_claim": True,
        }
        for family in TargetFamily
    ]


def _approval_gates() -> dict[str, dict[str, Any]]:
    return {
        "formal_artifact_review_gate": {
            "required_role_groups": list(REVIEWER_ROLE_GROUPS),
            "security_claim_requires_review": True,
            "security_claim_allowed_without_review": False,
            "unreviewed_proof_artifact_status": "pending_review",
        },
        "public_release_gate": {
            "required_role_groups": ["release_boundary_reviewer"],
            "requires_public_redaction": True,
            "private_data_publication_allowed": False,
            "security_claim_allowed_without_review": False,
        },
        "private_training_gate": {
            "required_role_groups": list(REVIEWER_ROLE_GROUPS),
            "requires_private_dataset_controls": True,
            "public_model_or_trace_publication_allowed": False,
            "security_claim_allowed_without_review": False,
        },
        "evolution_research_gate": {
            "required_role_groups": list(REVIEWER_ROLE_GROUPS),
            "requires_validator_pass": True,
            "requires_formal_obligations": True,
            "requires_human_review_before_claim": True,
            "security_claim_allowed_without_review": False,
        },
    }


def _required_reviewers_by_family() -> dict[str, list[str]]:
    return {
        family.value: required_reviewers_for_family(family)
        for family in TargetFamily
    }


def _verify_schema(governance: dict[str, Any], failures: list[str]) -> None:
    if governance.get("schema_version") != REVIEWER_GOVERNANCE_SCHEMA:
        failures.append(
            "Reviewer governance schema_version must be "
            f"{REVIEWER_GOVERNANCE_SCHEMA}."
        )


def _verify_role_groups(governance: dict[str, Any], failures: list[str]) -> None:
    role_groups = governance.get("role_groups")
    if not isinstance(role_groups, dict):
        failures.append("Reviewer governance role_groups must be an object.")
        return
    if sorted(role_groups) != sorted(REVIEWER_ROLE_GROUPS):
        failures.append("Reviewer governance role groups are incorrect.")
    family_group = _dict_or_empty(role_groups.get("family_cryptography_reviewer"))
    if family_group.get("minimum_reviewers_per_family_artifact") != 1:
        failures.append("Family reviewer group must require one reviewer per family.")
    if sorted(family_group.get("role_ids", [])) != sorted(
        set(FAMILY_REVIEWER_ROLE_IDS.values())
    ):
        failures.append("Family reviewer role IDs are not aligned with families.")


def _verify_family_reviewers(
    governance: dict[str, Any],
    failures: list[str],
) -> None:
    family_reviewers = governance.get("family_reviewers")
    if not isinstance(family_reviewers, list):
        failures.append("Reviewer governance family_reviewers must be a list.")
        return
    found_families = {
        entry.get("family")
        for entry in family_reviewers
        if isinstance(entry, dict)
    }
    if found_families != {family.value for family in TargetFamily}:
        failures.append(
            "Reviewer governance must define one family reviewer for each TargetFamily."
        )
    for entry in family_reviewers:
        if not isinstance(entry, dict):
            failures.append("Each family reviewer entry must be an object.")
            continue
        family = entry.get("family")
        if family not in FAMILY_REVIEWER_ROLE_IDS:
            failures.append(f"Family reviewer entry has unsupported family: {family}.")
            continue
        if entry.get("role_id") != FAMILY_REVIEWER_ROLE_IDS[family]:
            failures.append(f"Family reviewer role ID is incorrect: {family}.")
        if entry.get("role_group") != "family_cryptography_reviewer":
            failures.append(f"Family reviewer role group is incorrect: {family}.")
        if entry.get("minimum_reviewers") != 1:
            failures.append(f"Family reviewer minimum is incorrect: {family}.")
        if entry.get("assignment_status") != "role_required_unassigned":
            failures.append(
                f"Family reviewer assignment status is incorrect: {family}."
            )
        if not entry.get("required_expertise"):
            failures.append(f"Family reviewer expertise is missing: {family}.")
        if entry.get("required_before_security_claim") is not True:
            failures.append(
                f"Family reviewer must be required before security claims: {family}."
            )


def _verify_formal_backend_policy(
    governance: dict[str, Any],
    failures: list[str],
) -> None:
    policy = governance.get("formal_backend_policy")
    if not isinstance(policy, dict):
        failures.append("Reviewer governance formal_backend_policy must be an object.")
        return
    primary = _dict_or_empty(policy.get("primary"))
    smt = _dict_or_empty(policy.get("smt_assist"))
    if primary != {
        "backend": "lean4",
        "library": "mathlib",
        "required_for_security_claims": True,
    }:
        failures.append(
            "Reviewer governance primary formal backend must be Lean 4 + Mathlib."
        )
    if smt.get("backend") != "z3" or smt.get("scope") != (
        "optional_finite_decidable_obligations_only"
    ):
        failures.append(
            "SMT assistance must be scoped to finite decidable obligations."
        )
    if smt.get("may_replace_primary_backend") is not False:
        failures.append("SMT assistance must not replace the primary Lean backend.")


def _verify_approval_gates(
    governance: dict[str, Any],
    failures: list[str],
) -> None:
    gates = governance.get("approval_gates")
    if not isinstance(gates, dict):
        failures.append("Reviewer governance approval_gates must be an object.")
        return
    expected_gate_ids = {
        "formal_artifact_review_gate",
        "public_release_gate",
        "private_training_gate",
        "evolution_research_gate",
    }
    if set(gates) != expected_gate_ids:
        failures.append("Reviewer governance approval gates are incomplete.")
    formal_gate = _dict_or_empty(gates.get("formal_artifact_review_gate"))
    if formal_gate.get("required_role_groups") != REVIEWER_ROLE_GROUPS:
        failures.append("Formal artifact gate role groups are incorrect.")
    if formal_gate.get("security_claim_requires_review") is not True:
        failures.append("Security claims must require reviewer approval.")
    if formal_gate.get("security_claim_allowed_without_review") is not False:
        failures.append(
            "Security claims must not be allowed without domain and formal review."
        )
    if formal_gate.get("unreviewed_proof_artifact_status") != "pending_review":
        failures.append("Unreviewed proof artifacts must stay pending_review.")
    for gate_id, gate in gates.items():
        if not isinstance(gate, dict):
            failures.append(f"Approval gate {gate_id} must be an object.")
            continue
        if gate.get("security_claim_allowed_without_review") is not False:
            failures.append(f"Approval gate allows unreviewed claims: {gate_id}.")


def _verify_private_training_review(
    governance: dict[str, Any],
    failures: list[str],
) -> None:
    private = governance.get("private_training_review")
    if not isinstance(private, dict):
        failures.append(
            "Reviewer governance private_training_review must be an object."
        )
        return
    if private.get("publication_allowed") is not False:
        failures.append("Private training datasets must never be public.")
    if private.get("train_traces_publication_allowed") is not False:
        failures.append("Private training traces must never be public.")
    if private.get("reviewer_annotations_publication_allowed") is not False:
        failures.append("Private reviewer annotations must never be public.")
    if private.get("finetuned_qwen_publication_allowed") is not False:
        failures.append("Fine-tuned private Qwen must never be public.")
    if private.get("required_controls") != [
        "license_review",
        "provenance_tracking",
        "deduplication",
        "redaction",
        "contamination_audit",
    ]:
        failures.append("Private training review controls are incorrect.")


def _verify_formal_artifact_binding(
    governance: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    binding = _dict_or_empty(governance.get("formal_artifact_binding"))
    proof_artifacts = binding.get("mvp_vertical_proof_artifacts")
    if proof_artifacts != MVP_VERTICAL_PROOF_ARTIFACT_PATHS:
        failures.append("Formal artifact binding must include LWE and MLWE artifacts.")
        return
    required_by_family = _dict_or_empty(binding.get("required_reviewers_by_family"))
    for family_name, path_value in proof_artifacts.items():
        artifact = _read_json_object(
            root / path_value,
            "Formal proof artifact required by reviewer governance",
            failures,
        )
        if not artifact:
            continue
        if artifact.get("family") != family_name:
            failures.append(
                f"Formal proof artifact family mismatch: {path_value}."
            )
        expected_reviewers = required_by_family.get(family_name)
        if artifact.get("review", {}).get("required_reviewers") != expected_reviewers:
            failures.append("Formal proof artifact reviewers do not match governance.")
        if artifact.get("review", {}).get("status") not in REVIEW_STATUSES:
            failures.append("Formal proof artifact review status is unsupported.")
        claim_boundary = artifact.get("review", {}).get("claim_boundary", "")
        if binding.get("claim_boundary_contains") not in claim_boundary:
            failures.append("Formal proof artifact claim boundary is not explicit.")


def _verify_linked_artifacts(
    governance: dict[str, Any],
    expected: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    linked = governance.get("linked_artifacts")
    if not isinstance(linked, dict):
        failures.append("Reviewer governance linked_artifacts must be an object.")
        return
    if linked != expected.get("linked_artifacts"):
        failures.append("Reviewer governance linked artifact hashes are not in sync.")
    for name, artifact in linked.items():
        if not isinstance(artifact, dict):
            failures.append(f"Reviewer governance linked artifact {name} invalid.")
            continue
        path = artifact.get("path")
        if not isinstance(path, str) or not path:
            failures.append(f"Reviewer governance linked artifact {name} lacks path.")
            continue
        if not (root / path).is_file():
            failures.append(f"Reviewer governance linked artifact missing: {name}.")
        if artifact.get("sha256") is None:
            failures.append(f"Reviewer governance linked artifact lacks SHA: {name}.")


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


def _resolve_path(path: Path, root: Path) -> Path:
    return path if path.is_absolute() else root / path


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
