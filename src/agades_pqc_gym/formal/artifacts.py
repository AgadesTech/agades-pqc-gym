from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.target import SupportLevel, TargetFamily
from agades_pqc_gym.utils.hashing import stable_sha256

PROOF_ARTIFACT_SCHEMA = "agades.pqc.formal.proof_artifact.v1"
PROOF_ARTIFACT_VERIFICATION_SCHEMA = (
    "agades.pqc.formal.proof_artifact_verification.v1"
)
BACKEND = {
    "primary": "lean4",
    "library": "mathlib",
    "smt_assist": "z3_optional_finite_decidable_obligations_only",
}
ROOT = Path(__file__).resolve().parents[3]
LEAN_BACKEND_ROOT = Path("formal/lean")
LEAN_THEOREM_SOURCES = {
    "AgadesPQC.Lattice.Target.dimension_modulus_positive": (
        "formal/lean/AgadesPQC/Lattice/Target.lean"
    ),
    "AgadesPQC.Lattice.Target.distributions_present": (
        "formal/lean/AgadesPQC/Lattice/Target.lean"
    ),
    "AgadesPQC.Lattice.Target.parameters_positive": (
        "formal/lean/AgadesPQC/Lattice/Target.lean"
    ),
    "AgadesPQC.Lattice.PrimalUSVP.beta_valid_range": (
        "formal/lean/AgadesPQC/Lattice/PrimalUSVP.lean"
    ),
    "AgadesPQC.CodeBased.Target.parameters_well_formed": (
        "formal/lean/AgadesPQC/CodeBased/Target.lean"
    ),
    "AgadesPQC.CodeBased.SchemaOnly.no_estimate": (
        "formal/lean/AgadesPQC/CodeBased/SchemaOnly.lean"
    ),
    "AgadesPQC.Evaluator.no_security_claim": (
        "formal/lean/AgadesPQC/Evaluator.lean"
    ),
    "AgadesPQC.Generic.Target.family_shape_validated": (
        "formal/lean/AgadesPQC/Generic/Target.lean"
    ),
}
REQUIRED_REVIEWERS = [
    "lattice_cryptographer",
    "formal_methods_reviewer",
    "release_boundary_reviewer",
]
REVIEW_STATUSES = {"pending_review", "reviewed", "rejected"}


def build_attack_plan_proof_artifact(
    plan_path: Path,
    *,
    estimator_result_path: Path | None = None,
    review_status: str = "pending_review",
) -> dict[str, Any]:
    raw = plan_path.read_text(encoding="utf-8")
    plan = AttackPlan.model_validate_json(raw)
    plan_payload = json.loads(raw)
    if review_status not in REVIEW_STATUSES:
        raise ValueError(
            "review_status must be one of: " + ", ".join(sorted(REVIEW_STATUSES))
        )
    artifact: dict[str, Any] = {
        "schema_version": PROOF_ARTIFACT_SCHEMA,
        "backend": BACKEND,
        "formal_backend": {
            "root": LEAN_BACKEND_ROOT.as_posix(),
            "toolchain": (LEAN_BACKEND_ROOT / "lean-toolchain").as_posix(),
            "lakefile": (LEAN_BACKEND_ROOT / "lakefile.lean").as_posix(),
            "entry_module": (LEAN_BACKEND_ROOT / "AgadesPQC.lean").as_posix(),
            "execution_status": "not_run_in_this_environment",
        },
        "attack_plan": {
            "id": plan.attack_plan_id,
            "path": plan_path.as_posix(),
            "sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            "canonical_sha256": stable_sha256(plan_payload),
        },
        "family": plan.target.family.value,
        "operator_semantics": [
            _operator_semantics(operator.type) for operator in plan.operators
        ],
        "family_invariants": _family_invariants(plan),
        "estimator_model": _estimator_model(plan),
        "estimator_result_binding": _estimator_result_binding(estimator_result_path),
        "proof_obligations": _proof_obligations(plan),
        "review": {
            "status": review_status,
            "required_reviewers": REQUIRED_REVIEWERS,
            "claim_boundary": (
                "formal obligations are applicability checks, not PQC break claims"
            ),
        },
    }
    artifact["artifact_sha256"] = _artifact_sha256(artifact)
    return artifact


def write_attack_plan_proof_artifact(
    plan_path: Path,
    out: Path,
    *,
    estimator_result_path: Path | None = None,
    review_status: str = "pending_review",
) -> dict[str, Any]:
    artifact = build_attack_plan_proof_artifact(
        plan_path,
        estimator_result_path=estimator_result_path,
        review_status=review_status,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return artifact


def verify_attack_plan_proof_artifact(
    artifact_path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or Path.cwd()).resolve()
    failures: list[str] = []
    artifact = _read_json_object(artifact_path, failures)
    if artifact:
        _verify_artifact_shape(artifact, failures)
        _verify_artifact_hash(artifact, failures)
        _verify_plan_binding(artifact, project_root, failures)
        _verify_obligation_hashes(artifact, failures)
        _verify_estimator_result_binding(artifact, project_root, failures)
        _verify_review_binding(artifact, failures)

    summary = {
        "operator_semantics": len(artifact.get("operator_semantics", [])),
        "family_invariants": len(artifact.get("family_invariants", [])),
        "proof_obligations": len(artifact.get("proof_obligations", [])),
        "lean_theorems": len(
            {
                obligation.get("lean_theorem")
                for obligation in artifact.get("proof_obligations", [])
                if obligation.get("lean_theorem")
            }
        ),
        "estimator_result_attached": (
            artifact.get("estimator_result_binding", {}).get("status")
            == "attached_unreviewed"
        ),
        "required_reviewers": len(
            artifact.get("review", {}).get("required_reviewers", [])
        ),
        "failure_count": len(failures),
    }
    return {
        "schema_version": PROOF_ARTIFACT_VERIFICATION_SCHEMA,
        "artifact_path": artifact_path.as_posix(),
        "accepted": not failures,
        "summary": summary,
        "failures": failures,
    }


def _operator_semantics(operator_type: str) -> dict[str, str]:
    if operator_type == "primal_usvp":
        return {
            "operator": operator_type,
            "semantics_id": "agades.pqc.operator_semantics.lattice.primal_usvp.v1",
            "lean_namespace": "AgadesPQC.Lattice.PrimalUSVP",
        }
    if operator_type == "information_set_decoding":
        return {
            "operator": operator_type,
            "semantics_id": "agades.pqc.operator_semantics.code_based.isd.v1",
            "lean_namespace": "AgadesPQC.CodeBased.ISD",
        }
    return {
        "operator": operator_type,
        "semantics_id": f"agades.pqc.operator_semantics.generic.{operator_type}.v1",
        "lean_namespace": "AgadesPQC.Generic",
    }


def _family_invariants(plan: AttackPlan) -> list[dict[str, str]]:
    family = plan.target.family
    if family in {TargetFamily.LWE, TargetFamily.MLWE}:
        return [
            {
                "invariant_id": "lattice.dimension_modulus_positive",
                "statement": "n > 0 and q > 1",
                "lean_theorem": "AgadesPQC.Lattice.Target.dimension_modulus_positive",
            }
            | _lean_source(
                "AgadesPQC.Lattice.Target.dimension_modulus_positive"
            ),
            {
                "invariant_id": "lattice.distributions_present",
                "statement": "secret and error distributions are present for LWE/MLWE",
                "lean_theorem": "AgadesPQC.Lattice.Target.distributions_present",
            }
            | _lean_source("AgadesPQC.Lattice.Target.distributions_present"),
        ]
    if family is TargetFamily.CODE_BASED:
        return [
            {
                "invariant_id": "code_based.length_dimension_weight_positive",
                "statement": "n > 0, k > 0, w > 0, and k <= n",
                "lean_theorem": "AgadesPQC.CodeBased.Target.parameters_well_formed",
            }
            | _lean_source("AgadesPQC.CodeBased.Target.parameters_well_formed")
        ]
    return [
        {
            "invariant_id": f"{family.value.lower()}.family_shape_validated",
            "statement": "TargetSpec family-specific validator accepted the shape",
            "lean_theorem": "AgadesPQC.Generic.Target.family_shape_validated",
        }
        | _lean_source("AgadesPQC.Generic.Target.family_shape_validated")
    ]


def _estimator_model(plan: AttackPlan) -> dict[str, Any]:
    if plan.target.support_level is SupportLevel.SCHEMA_ONLY:
        return {
            "status": "unsupported",
            "model_id": "schema_only_no_estimator",
            "no_fake_estimate": True,
        }
    return {
        "status": "result_binding_required_before_claim",
        "model_id": "agades.pqc.evaluator_model.boundary.v1",
        "no_fake_estimate": True,
    }


def _estimator_result_binding(
    estimator_result_path: Path | None,
) -> dict[str, Any]:
    if estimator_result_path is None:
        return {
            "status": "not_attached",
            "path": None,
            "sha256": None,
            "canonical_sha256": None,
            "claim_allowed": False,
            "notes": (
                "No estimator result is attached; the artifact cannot support "
                "a security claim."
            ),
        }

    raw = estimator_result_path.read_bytes()
    try:
        canonical_payload: Any = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        canonical_payload = raw.decode("utf-8", errors="replace")
    return {
        "status": "attached_unreviewed",
        "path": estimator_result_path.as_posix(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "canonical_sha256": stable_sha256(canonical_payload),
        "claim_allowed": False,
        "notes": (
            "Estimator output is bound for reproducibility and reviewer "
            "inspection; it is not a reviewed cryptographic claim."
        ),
    }


def _proof_obligations(plan: AttackPlan) -> list[dict[str, Any]]:
    family = plan.target.family
    obligations: list[dict[str, Any]] = []
    if family in {TargetFamily.LWE, TargetFamily.MLWE}:
        obligations.extend(
            [
                _obligation(
                    "target.lwe.parameters.positive",
                    (
                        "Target parameters satisfy n > 0, q > 1, and m/k bounds "
                        "where present."
                    ),
                    "AgadesPQC.Lattice.Target.parameters_positive",
                ),
                _obligation(
                    "target.lwe.distributions.present",
                    "Secret and error distributions are specified for LWE/MLWE.",
                    "AgadesPQC.Lattice.Target.distributions_present",
                ),
            ]
        )
    if any(operator.type == "primal_usvp" for operator in plan.operators):
        obligations.append(
            _obligation(
                "operator.primal_usvp.beta.valid_range",
                (
                    "primal_usvp beta is positive and bounded by the target "
                    "dimension policy."
                ),
                "AgadesPQC.Lattice.PrimalUSVP.beta_valid_range",
            )
        )
    if (
        family is TargetFamily.CODE_BASED
        and plan.target.support_level is SupportLevel.SCHEMA_ONLY
    ):
        obligations.append(
            _obligation(
                "family.code_based.schema_only.no_estimate",
                "Schema-only code-based plans must not emit cryptanalytic estimates.",
                "AgadesPQC.CodeBased.SchemaOnly.no_estimate",
            )
        )
    obligations.append(
        _obligation(
            "estimator.boundary.no_security_claim",
            (
                "Evaluator outputs are analytical or toy plumbing results, not "
                "security-break proofs."
            ),
            "AgadesPQC.Evaluator.no_security_claim",
        )
    )
    return obligations


def _obligation(
    obligation_id: str,
    statement: str,
    lean_theorem: str,
) -> dict[str, Any]:
    payload = {
        "obligation_id": obligation_id,
        "statement": statement,
        "backend": "lean4",
        "lean_theorem": lean_theorem,
        **_lean_source(lean_theorem),
        "status": "pending_review",
    }
    return {
        **payload,
        "obligation_sha256": stable_sha256(payload),
    }


def _artifact_sha256(artifact: dict[str, Any]) -> str:
    payload = {
        key: value for key, value in artifact.items() if key != "artifact_sha256"
    }
    return stable_sha256(payload)


def _lean_source(lean_theorem: str) -> dict[str, Any]:
    path = LEAN_THEOREM_SOURCES[lean_theorem]
    declaration = lean_theorem.rsplit(".", 1)[1]
    source_path = ROOT / path
    return {
        "lean_source": {
            "path": path,
            "sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
            "declaration": declaration,
        }
    }


def _read_json_object(path: Path, failures: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"Proof artifact is missing: {path.as_posix()}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(f"Proof artifact is invalid JSON at line {exc.lineno}.")
        return {}
    if not isinstance(payload, dict):
        failures.append("Proof artifact must be a JSON object.")
        return {}
    return payload


def _verify_artifact_shape(
    artifact: dict[str, Any],
    failures: list[str],
) -> None:
    if artifact.get("schema_version") != PROOF_ARTIFACT_SCHEMA:
        failures.append(
            f"Proof artifact schema_version must be {PROOF_ARTIFACT_SCHEMA}."
        )
    if artifact.get("backend") != BACKEND:
        failures.append("Proof artifact backend must be Lean 4 + Mathlib.")
    for key in (
        "attack_plan",
        "operator_semantics",
        "family_invariants",
        "estimator_model",
        "estimator_result_binding",
        "proof_obligations",
        "review",
        "artifact_sha256",
    ):
        if key not in artifact:
            failures.append(f"Proof artifact is missing {key}.")
    _verify_formal_backend(artifact, failures)


def _verify_artifact_hash(
    artifact: dict[str, Any],
    failures: list[str],
) -> None:
    if artifact.get("artifact_sha256") != _artifact_sha256(artifact):
        failures.append("Proof artifact hash does not match its payload.")


def _verify_plan_binding(
    artifact: dict[str, Any],
    project_root: Path,
    failures: list[str],
) -> None:
    attack_plan = artifact.get("attack_plan", {})
    if not isinstance(attack_plan, dict):
        failures.append("Proof artifact attack_plan must be a JSON object.")
        return

    plan_path_value = attack_plan.get("path")
    if not isinstance(plan_path_value, str) or not plan_path_value:
        failures.append("Proof artifact attack_plan.path is required.")
        return

    plan_path = Path(plan_path_value)
    if not plan_path.is_absolute():
        plan_path = project_root / plan_path
    try:
        raw = plan_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        failures.append(f"Bound AttackPlan is missing: {plan_path_value}.")
        return

    if attack_plan.get("sha256") != hashlib.sha256(raw.encode("utf-8")).hexdigest():
        failures.append("AttackPlan raw SHA-256 does not match the bound file.")
    try:
        plan_payload = json.loads(raw)
        plan = AttackPlan.model_validate(plan_payload)
    except Exception as exc:  # noqa: BLE001
        failures.append(f"Bound AttackPlan is invalid: {exc}")
        return

    if attack_plan.get("canonical_sha256") != stable_sha256(plan_payload):
        failures.append("AttackPlan canonical SHA-256 does not match the bound file.")
    if attack_plan.get("id") != plan.attack_plan_id:
        failures.append("AttackPlan id does not match the bound file.")
    if artifact.get("family") != plan.target.family.value:
        failures.append("Proof artifact family does not match the AttackPlan.")
    if artifact.get("operator_semantics") != [
        _operator_semantics(operator.type) for operator in plan.operators
    ]:
        failures.append("Operator semantics do not match the AttackPlan.")
    if artifact.get("family_invariants") != _family_invariants(plan):
        failures.append("Family invariants do not match the AttackPlan.")
    if artifact.get("estimator_model") != _estimator_model(plan):
        failures.append("Estimator model does not match the AttackPlan.")
    if artifact.get("proof_obligations") != _proof_obligations(plan):
        failures.append("Proof obligations do not match the AttackPlan.")
    _verify_lean_bindings(artifact, project_root, failures)


def _verify_obligation_hashes(
    artifact: dict[str, Any],
    failures: list[str],
) -> None:
    obligations = artifact.get("proof_obligations", [])
    if not isinstance(obligations, list):
        failures.append("Proof obligations must be a list.")
        return
    for obligation in obligations:
        if not isinstance(obligation, dict):
            failures.append("Each proof obligation must be a JSON object.")
            continue
        payload = {
            key: obligation.get(key)
            for key in (
                "obligation_id",
                "statement",
                "backend",
                "lean_theorem",
                "lean_source",
                "status",
            )
        }
        if obligation.get("backend") != "lean4":
            failures.append("Proof obligations must target lean4.")
        if not obligation.get("lean_theorem"):
            failures.append("Proof obligations must bind a Lean theorem.")
        if obligation.get("obligation_sha256") != stable_sha256(payload):
            failures.append(
                f"Proof obligation hash mismatch: {obligation.get('obligation_id')}."
            )


def _verify_formal_backend(
    artifact: dict[str, Any],
    failures: list[str],
) -> None:
    formal_backend = artifact.get("formal_backend")
    if not isinstance(formal_backend, dict):
        failures.append("Proof artifact formal_backend must be a JSON object.")
        return
    expected = {
        "root": "formal/lean",
        "toolchain": "formal/lean/lean-toolchain",
        "lakefile": "formal/lean/lakefile.lean",
        "entry_module": "formal/lean/AgadesPQC.lean",
        "execution_status": "not_run_in_this_environment",
    }
    if formal_backend != expected:
        failures.append("Proof artifact formal_backend is incorrect.")


def _verify_lean_bindings(
    artifact: dict[str, Any],
    project_root: Path,
    failures: list[str],
) -> None:
    entries = [
        *artifact.get("family_invariants", []),
        *artifact.get("proof_obligations", []),
    ]
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        lean_theorem = entry.get("lean_theorem")
        source = entry.get("lean_source")
        if not isinstance(lean_theorem, str) or not lean_theorem:
            failures.append("Lean-bound entry is missing lean_theorem.")
            continue
        if not isinstance(source, dict):
            failures.append(f"Lean theorem {lean_theorem} is missing lean_source.")
            continue
        expected_path = LEAN_THEOREM_SOURCES.get(lean_theorem)
        if source.get("path") != expected_path:
            failures.append(f"Lean theorem {lean_theorem} has wrong source path.")
            continue
        source_path = project_root / expected_path
        try:
            raw = source_path.read_bytes()
        except FileNotFoundError:
            failures.append(f"Lean source is missing: {expected_path}.")
            continue
        if source.get("sha256") != hashlib.sha256(raw).hexdigest():
            failures.append(f"Lean source hash mismatch: {expected_path}.")
        declaration = lean_theorem.rsplit(".", 1)[1]
        if source.get("declaration") != declaration:
            failures.append(f"Lean theorem {lean_theorem} declaration drifted.")
        if f"theorem {declaration}" not in raw.decode("utf-8"):
            failures.append(f"Lean theorem {lean_theorem} is missing from source.")


def _verify_estimator_result_binding(
    artifact: dict[str, Any],
    project_root: Path,
    failures: list[str],
) -> None:
    binding = artifact.get("estimator_result_binding", {})
    if not isinstance(binding, dict):
        failures.append("Estimator result binding must be a JSON object.")
        return
    if binding.get("claim_allowed") is not False:
        failures.append("Estimator result binding must not allow security claims.")
    status = binding.get("status")
    if status == "not_attached":
        if binding.get("path") is not None or binding.get("sha256") is not None:
            failures.append("Detached estimator binding must not carry a path or hash.")
        return
    if status != "attached_unreviewed":
        failures.append("Estimator result binding status is unsupported.")
        return

    result_path_value = binding.get("path")
    if not isinstance(result_path_value, str) or not result_path_value:
        failures.append("Attached estimator result binding requires a path.")
        return
    result_path = Path(result_path_value)
    if not result_path.is_absolute():
        result_path = project_root / result_path
    try:
        raw = result_path.read_bytes()
    except FileNotFoundError:
        failures.append(f"Bound estimator result is missing: {result_path_value}.")
        return
    if binding.get("sha256") != hashlib.sha256(raw).hexdigest():
        failures.append("Estimator result SHA-256 does not match the bound file.")
    try:
        canonical_payload: Any = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        canonical_payload = raw.decode("utf-8", errors="replace")
    if binding.get("canonical_sha256") != stable_sha256(canonical_payload):
        failures.append(
            "Estimator result canonical SHA-256 does not match the bound file."
        )


def _verify_review_binding(
    artifact: dict[str, Any],
    failures: list[str],
) -> None:
    review = artifact.get("review", {})
    if not isinstance(review, dict):
        failures.append("Proof artifact review must be a JSON object.")
        return
    if review.get("status") not in REVIEW_STATUSES:
        failures.append("Proof artifact review status is unsupported.")
    if review.get("required_reviewers") != REQUIRED_REVIEWERS:
        failures.append("Proof artifact required reviewers are incorrect.")
    if "not PQC break claims" not in review.get("claim_boundary", ""):
        failures.append("Proof artifact must state the no-overclaim boundary.")
