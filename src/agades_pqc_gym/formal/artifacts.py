from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.evaluator_result import EvaluatorResult
from agades_pqc_gym.core.target import SupportLevel, TargetFamily
from agades_pqc_gym.formal.review import (
    REVIEW_STATUSES,
    required_reviewers_for_family,
)
from agades_pqc_gym.utils.hashing import stable_sha256

PROOF_ARTIFACT_SCHEMA = "agades.pqc.formal.proof_artifact.v1"
PROOF_ARTIFACT_VERIFICATION_SCHEMA = (
    "agades.pqc.formal.proof_artifact_verification.v1"
)
ATTACK_PLAN_SCHEMA_CONTRACT_SCHEMA = "agades.pqc.attack_plan.schema_contract.v1"
ATTACK_PLAN_SCHEMA_MODEL = "agades_pqc_gym.core.attack_plan.AttackPlan"
ATTACK_PLAN_CANONICALIZATION = "json_sort_keys_minified_v1"
ATTACK_PLAN_VALIDATION = "pydantic_v2_extra_forbid_family_cross_checks"
REVIEW_EVIDENCE_SCHEMA = "agades.pqc.formal.review_evidence.v1"
EVALUATOR_RESULT_SCHEMA_CONTRACT_SCHEMA = (
    "agades.pqc.evaluator_result.schema_contract.v1"
)
EVALUATOR_RESULT_SCHEMA_MODEL = "agades_pqc_gym.core.evaluator_result.EvaluatorResult"
EVALUATOR_RESULT_VALIDATION = "pydantic_v2_extra_forbid_status_payload_checks"
ESTIMATOR_ATTACK_TYPE_COMPATIBILITY_RULE = "exact_operator_or_colon_variant_v1"
PROOF_OBLIGATION_TYPE_SCHEMA = "agades.pqc.formal.proof_obligation_type.v1"
PROOF_OBLIGATION_TYPE_RULE_SCHEMA = (
    "agades.pqc.formal.proof_obligation_type_rule.v1"
)
PROOF_OBLIGATION_CLAIM_POLICY = {
    "public_interpretation": "applicability_check_only",
    "review_required_before_claim": True,
    "security_claim_allowed": False,
}
PROOF_OBLIGATION_TYPE_KINDS = {
    "target_invariant",
    "operator_precondition",
    "schema_only_boundary",
    "family_applicability_boundary",
    "estimator_claim_boundary",
}
BACKEND = {
    "primary": "lean4",
    "library": "mathlib",
    "smt_assist": "z3_optional_finite_decidable_obligations_only",
}
ROOT = Path(__file__).resolve().parents[3]
LEAN_BACKEND_ROOT = Path("formal/lean")
FORMAL_LEAN_BACKEND_PATH = Path("docs/formal_lean_backend.json")
MVP_VERTICAL_PROOF_ARTIFACT_PATHS = {
    TargetFamily.LWE.value: "docs/formal_lattice_primal_usvp_proof_artifact.json",
    TargetFamily.MLWE.value: (
        "docs/formal_lattice_mlwe_module_hypothesis_proof_artifact.json"
    ),
}
MVP_VERTICAL_ESTIMATOR_RESULT_PATHS = {
    TargetFamily.LWE.value: (
        "docs/formal_lattice_primal_usvp_evaluator_result.json"
    ),
    TargetFamily.MLWE.value: (
        "docs/formal_lattice_mlwe_module_hypothesis_evaluator_result.json"
    ),
}
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
    "AgadesPQC.Lattice.Target.module_rank_present": (
        "formal/lean/AgadesPQC/Lattice/Target.lean"
    ),
    "AgadesPQC.Lattice.Target.ntru_schema_shape": (
        "formal/lean/AgadesPQC/Lattice/Target.lean"
    ),
    "AgadesPQC.Lattice.Target.sis_schema_shape": (
        "formal/lean/AgadesPQC/Lattice/Target.lean"
    ),
    "AgadesPQC.Lattice.Target.ntru_schema_only_no_estimate": (
        "formal/lean/AgadesPQC/Lattice/Target.lean"
    ),
    "AgadesPQC.Lattice.Target.sis_schema_only_no_estimate": (
        "formal/lean/AgadesPQC/Lattice/Target.lean"
    ),
    "AgadesPQC.Lattice.PrimalUSVP.beta_valid_range": (
        "formal/lean/AgadesPQC/Lattice/PrimalUSVP.lean"
    ),
    "AgadesPQC.EstimatorModel.operator_compatibility_declared": (
        "formal/lean/AgadesPQC/EstimatorModel.lean"
    ),
    "AgadesPQC.EstimatorModel.result_binding_required_before_claim": (
        "formal/lean/AgadesPQC/EstimatorModel.lean"
    ),
    "AgadesPQC.EstimatorModel.schema_only_no_estimator": (
        "formal/lean/AgadesPQC/EstimatorModel.lean"
    ),
    "AgadesPQC.OperatorSemantics.required_parameter_bound": (
        "formal/lean/AgadesPQC/OperatorSemantics.lean"
    ),
    "AgadesPQC.OperatorSemantics.family_binding_valid": (
        "formal/lean/AgadesPQC/OperatorSemantics.lean"
    ),
    "AgadesPQC.OperatorSemantics.unreviewed_security_claim_forbidden": (
        "formal/lean/AgadesPQC/OperatorSemantics.lean"
    ),
    "AgadesPQC.ProofObligation.target_invariant_typed": (
        "formal/lean/AgadesPQC/ProofObligation.lean"
    ),
    "AgadesPQC.ProofObligation.operator_precondition_typed": (
        "formal/lean/AgadesPQC/ProofObligation.lean"
    ),
    "AgadesPQC.ProofObligation.schema_only_boundary_typed": (
        "formal/lean/AgadesPQC/ProofObligation.lean"
    ),
    "AgadesPQC.ProofObligation.family_applicability_boundary_typed": (
        "formal/lean/AgadesPQC/ProofObligation.lean"
    ),
    "AgadesPQC.ProofObligation.estimator_claim_boundary_typed": (
        "formal/lean/AgadesPQC/ProofObligation.lean"
    ),
    "AgadesPQC.CodeBased.Target.parameters_well_formed": (
        "formal/lean/AgadesPQC/CodeBased/Target.lean"
    ),
    "AgadesPQC.CodeBased.SchemaOnly.no_estimate": (
        "formal/lean/AgadesPQC/CodeBased/SchemaOnly.lean"
    ),
    "AgadesPQC.Multivariate.Target.variables_equations_field_present": (
        "formal/lean/AgadesPQC/Multivariate/Target.lean"
    ),
    "AgadesPQC.Multivariate.Target.applicability_shape": (
        "formal/lean/AgadesPQC/Multivariate/Target.lean"
    ),
    "AgadesPQC.HashBased.Target.hash_function_and_security_parameter_present": (
        "formal/lean/AgadesPQC/HashBased/Target.lean"
    ),
    "AgadesPQC.HashBased.Target.bound_check_is_not_attack_claim": (
        "formal/lean/AgadesPQC/HashBased/Target.lean"
    ),
    "AgadesPQC.IsogenyHistorical.Target.dimension_positive_historical_scope": (
        "formal/lean/AgadesPQC/IsogenyHistorical/Target.lean"
    ),
    "AgadesPQC.IsogenyHistorical.Target.historical_only": (
        "formal/lean/AgadesPQC/IsogenyHistorical/Target.lean"
    ),
    "AgadesPQC.ImplementationSecurity.Target.review_scope_declared": (
        "formal/lean/AgadesPQC/ImplementationSecurity/Target.lean"
    ),
    "AgadesPQC.ImplementationSecurity.Target.no_conformance_claim": (
        "formal/lean/AgadesPQC/ImplementationSecurity/Target.lean"
    ),
    "AgadesPQC.Evaluator.no_security_claim": (
        "formal/lean/AgadesPQC/Evaluator.lean"
    ),
    "AgadesPQC.Evaluator.attached_unreviewed_no_security_claim": (
        "formal/lean/AgadesPQC/Evaluator.lean"
    ),
    "AgadesPQC.Evaluator.schema_only_no_estimator_no_security_claim": (
        "formal/lean/AgadesPQC/Evaluator.lean"
    ),
    "AgadesPQC.Generic.Target.family_shape_validated": (
        "formal/lean/AgadesPQC/Generic/Target.lean"
    ),
}
PROOF_OBLIGATION_TYPE_RULES = {
    "target_invariant": {
        "statement": (
            "Target invariant obligations are typed as target-scoped Lean "
            "obligations with reviewer-gated, non-security-claim semantics."
        ),
        "lean_theorem": "AgadesPQC.ProofObligation.target_invariant_typed",
    },
    "operator_precondition": {
        "statement": (
            "Operator precondition obligations are typed as operator-scoped "
            "Lean obligations with reviewer-gated, non-security-claim semantics."
        ),
        "lean_theorem": "AgadesPQC.ProofObligation.operator_precondition_typed",
    },
    "schema_only_boundary": {
        "statement": (
            "Schema-only boundary obligations are typed as estimator-boundary "
            "Lean obligations that forbid fake runtime estimates."
        ),
        "lean_theorem": "AgadesPQC.ProofObligation.schema_only_boundary_typed",
    },
    "family_applicability_boundary": {
        "statement": (
            "Family applicability boundary obligations are typed as "
            "family-scoped Lean obligations with no public security claim."
        ),
        "lean_theorem": (
            "AgadesPQC.ProofObligation.family_applicability_boundary_typed"
        ),
    },
    "estimator_claim_boundary": {
        "statement": (
            "Estimator claim boundary obligations are typed as estimator-scoped "
            "Lean obligations that require review before any security claim."
        ),
        "lean_theorem": "AgadesPQC.ProofObligation.estimator_claim_boundary_typed",
    },
}
OPERATOR_SEMANTICS = {
    "primal_usvp": (
        "agades.pqc.operator_semantics.lattice.primal_usvp.v1",
        "AgadesPQC.Lattice.PrimalUSVP",
    ),
    "bounded_distance_decoding": (
        "agades.pqc.operator_semantics.lattice.bdd.v1",
        "AgadesPQC.Lattice.BDD",
    ),
    "dual_attack": (
        "agades.pqc.operator_semantics.lattice.dual_attack.v1",
        "AgadesPQC.Lattice.DualAttack",
    ),
    "dual_hybrid": (
        "agades.pqc.operator_semantics.lattice.dual_hybrid.v1",
        "AgadesPQC.Lattice.DualHybrid",
    ),
    "bkw": (
        "agades.pqc.operator_semantics.lattice.bkw.v1",
        "AgadesPQC.Lattice.BKW",
    ),
    "modulus_switching": (
        "agades.pqc.operator_semantics.lattice.modulus_switching.v1",
        "AgadesPQC.Lattice.ModulusSwitching",
    ),
    "sample_selection": (
        "agades.pqc.operator_semantics.lattice.sample_selection.v1",
        "AgadesPQC.Lattice.SampleSelection",
    ),
    "secret_guessing": (
        "agades.pqc.operator_semantics.lattice.secret_guessing.v1",
        "AgadesPQC.Lattice.SecretGuessing",
    ),
    "meet_in_the_middle": (
        "agades.pqc.operator_semantics.lattice.meet_in_the_middle.v1",
        "AgadesPQC.Lattice.MeetInTheMiddle",
    ),
    "normal_form_transform": (
        "agades.pqc.operator_semantics.lattice.normal_form_transform.v1",
        "AgadesPQC.Lattice.NormalFormTransform",
    ),
    "bkz_parameter_sweep": (
        "agades.pqc.operator_semantics.lattice.bkz_parameter_sweep.v1",
        "AgadesPQC.Lattice.BKZParameterSweep",
    ),
    "module_lattice_reduction_hypothesis": (
        "agades.pqc.operator_semantics.lattice.module_reduction_hypothesis.v1",
        "AgadesPQC.Lattice.ModuleReductionHypothesis",
    ),
    "decoding_fixture_check": (
        "agades.pqc.operator_semantics.code_based.decoding_fixture_check.v1",
        "AgadesPQC.CodeBased.DecodingFixtureCheck",
    ),
    "information_set_decoding": (
        "agades.pqc.operator_semantics.code_based.isd.v1",
        "AgadesPQC.CodeBased.ISD",
    ),
    "minrank_attack": (
        "agades.pqc.operator_semantics.multivariate.minrank_attack.v1",
        "AgadesPQC.Multivariate.MinRank",
    ),
    "groebner_basis": (
        "agades.pqc.operator_semantics.multivariate.groebner_basis.v1",
        "AgadesPQC.Multivariate.GroebnerBasis",
    ),
    "signature_fixture_check": (
        "agades.pqc.operator_semantics.multivariate.signature_fixture_check.v1",
        "AgadesPQC.Multivariate.SignatureFixtureCheck",
    ),
    "security_bound_check": (
        "agades.pqc.operator_semantics.hash_based.security_bound_check.v1",
        "AgadesPQC.HashBased.SecurityBoundCheck",
    ),
    "hash_signature_verification": (
        "agades.pqc.operator_semantics.hash_based.signature_verification.v1",
        "AgadesPQC.HashBased.SignatureVerification",
    ),
    "misuse_check": (
        "agades.pqc.operator_semantics.hash_based.misuse_check.v1",
        "AgadesPQC.HashBased.MisuseCheck",
    ),
    "historical_isogeny_reconstruction": (
        "agades.pqc.operator_semantics.isogeny_historical.reconstruction.v1",
        "AgadesPQC.IsogenyHistorical.Reconstruction",
    ),
    "kat_conformance": (
        "agades.pqc.operator_semantics.implementation_security.kat_conformance.v1",
        "AgadesPQC.ImplementationSecurity.KATConformance",
    ),
    "constant_time_check": (
        "agades.pqc.operator_semantics.implementation_security.constant_time_check.v1",
        "AgadesPQC.ImplementationSecurity.ConstantTimeCheck",
    ),
    "benchmark_harness": (
        "agades.pqc.operator_semantics.implementation_security.benchmark_harness.v1",
        "AgadesPQC.ImplementationSecurity.BenchmarkHarness",
    ),
}


def build_attack_plan_proof_artifact(
    plan_path: Path,
    *,
    estimator_result_path: Path | None = None,
    review_status: str = "pending_review",
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = root.resolve() if root is not None else None
    resolved_plan_path = plan_path
    if project_root is not None and not resolved_plan_path.is_absolute():
        resolved_plan_path = project_root / resolved_plan_path
    raw = resolved_plan_path.read_text(encoding="utf-8")
    return build_attack_plan_proof_artifact_from_json(
        raw,
        source_label=plan_path.as_posix(),
        estimator_result_path=estimator_result_path,
        review_status=review_status,
        root=project_root,
    )


def build_attack_plan_proof_artifact_from_json(
    raw_json: str,
    *,
    source_label: str,
    estimator_result_path: Path | None = None,
    review_status: str = "pending_review",
    root: Path | None = None,
) -> dict[str, Any]:
    plan = AttackPlan.model_validate_json(raw_json)
    plan_payload = json.loads(raw_json)
    project_root = root.resolve() if root is not None else ROOT
    if review_status not in REVIEW_STATUSES:
        raise ValueError(
            "review_status must be one of: " + ", ".join(sorted(REVIEW_STATUSES))
        )
    if review_status != "pending_review":
        raise ValueError(
            "review evidence is required for non-pending proof artifacts"
        )
    required_reviewers = required_reviewers_for_family(plan.target.family)
    artifact: dict[str, Any] = {
        "schema_version": PROOF_ARTIFACT_SCHEMA,
        "backend": BACKEND,
        "formal_backend": _formal_backend_binding(project_root),
        "attack_plan": {
            "id": plan.attack_plan_id,
            "path": source_label,
            "schema_contract": _attack_plan_schema_contract(),
            "sha256": hashlib.sha256(raw_json.encode("utf-8")).hexdigest(),
            "canonical_sha256": stable_sha256(plan_payload),
        },
        "family": plan.target.family.value,
        "operator_semantics": [
            _operator_semantics(operator.type) for operator in plan.operators
        ],
        "family_invariants": _family_invariants(plan),
        "estimator_model": _estimator_model(plan),
        "proof_obligation_type_rules": proof_obligation_type_rules(),
        "estimator_result_binding": _estimator_result_binding(
            plan,
            estimator_result_path,
            root=project_root,
        ),
        "proof_obligations": _proof_obligations(plan),
        "review": {
            "status": review_status,
            "required_reviewers": required_reviewers,
            "evidence": _pending_review_evidence(),
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
    root: Path | None = None,
) -> dict[str, Any]:
    artifact = build_attack_plan_proof_artifact(
        plan_path,
        estimator_result_path=estimator_result_path,
        review_status=review_status,
        root=root,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return artifact


def write_attack_plan_evaluator_result(
    plan_path: Path,
    out: Path,
) -> dict[str, Any]:
    from agades_pqc_gym.evaluators.cascade import CascadeEvaluator

    raw = plan_path.read_text(encoding="utf-8")
    plan = AttackPlan.model_validate_json(raw)
    result = CascadeEvaluator().evaluate_plan(plan)
    if result.estimator_result is None:
        raise ValueError("AttackPlan evaluation did not produce an evaluator result")

    payload = result.estimator_result.model_dump(mode="json")
    raw_output = dict(payload.get("raw_output") or {})
    raw_output.update(
        {
            "source": "agades_pqc_gym.evaluators.cascade.CascadeEvaluator",
            "attack_plan_id": plan.attack_plan_id,
            "claim_allowed": False,
            "public_interpretation": (
                "reproducibility_and_reviewer_binding_only"
            ),
        }
    )
    payload["raw_output"] = raw_output

    warnings = list(payload.get("warnings") or [])
    for warning in result.warnings:
        if warning not in warnings:
            warnings.append(warning)
    binding_warning = (
        "Evaluator result is bound for reproducibility and reviewer inspection; "
        "it is not cryptanalytic evidence."
    )
    if binding_warning not in warnings:
        warnings.append(binding_warning)
    payload["warnings"] = warnings

    validated = EvaluatorResult.model_validate(payload)
    payload = validated.model_dump(mode="json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


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
        _verify_formal_backend(artifact, project_root, failures)
        _verify_artifact_hash(artifact, failures)
        _verify_plan_binding(artifact, project_root, failures)
        _verify_obligation_hashes(artifact, project_root, failures)
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
    from agades_pqc_gym.formal.operator_semantics import operator_semantics_entry

    return operator_semantics_entry(operator_type)


def _family_invariants(plan: AttackPlan) -> list[dict[str, Any]]:
    family = plan.target.family
    if family is TargetFamily.LWE:
        return _lwe_lattice_invariants()
    if family is TargetFamily.MLWE:
        return [
            *_lwe_lattice_invariants(),
            {
                "invariant_id": "lattice.mlwe.module_rank_present",
                "statement": "MLWE module rank k is present and positive",
                "lean_theorem": "AgadesPQC.Lattice.Target.module_rank_present",
            }
            | _lean_source("AgadesPQC.Lattice.Target.module_rank_present"),
        ]
    if family is TargetFamily.NTRU:
        return [
            {
                "invariant_id": "lattice.ntru.schema_shape",
                "statement": (
                    "NTRU schema-only targets carry positive n/q parameters "
                    "and a secret distribution"
                ),
                "lean_theorem": "AgadesPQC.Lattice.Target.ntru_schema_shape",
            }
            | _lean_source("AgadesPQC.Lattice.Target.ntru_schema_shape")
        ]
    if family is TargetFamily.SIS:
        return [
            {
                "invariant_id": "lattice.sis.schema_shape",
                "statement": (
                    "SIS schema-only targets carry positive n/q parameters "
                    "and a bounded secret distribution"
                ),
                "lean_theorem": "AgadesPQC.Lattice.Target.sis_schema_shape",
            }
            | _lean_source("AgadesPQC.Lattice.Target.sis_schema_shape")
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
    if family is TargetFamily.MULTIVARIATE:
        return [
            {
                "invariant_id": "multivariate.variables_equations_field_present",
                "statement": "variables > 0, equations > 0, and field is present",
                "lean_theorem": (
                    "AgadesPQC.Multivariate.Target."
                    "variables_equations_field_present"
                ),
            }
            | _lean_source(
                "AgadesPQC.Multivariate.Target."
                "variables_equations_field_present"
            )
        ]
    if family is TargetFamily.HASH_BASED:
        return [
            {
                "invariant_id": (
                    "hash_based.hash_function_and_security_parameter_present"
                ),
                "statement": "hash_function is present and n > 0 when provided",
                "lean_theorem": (
                    "AgadesPQC.HashBased.Target."
                    "hash_function_and_security_parameter_present"
                ),
            }
            | _lean_source(
                "AgadesPQC.HashBased.Target."
                "hash_function_and_security_parameter_present"
            )
        ]
    if family is TargetFamily.ISOGENY_HISTORICAL:
        return [
            {
                "invariant_id": (
                    "isogeny_historical.dimension_positive_historical_scope"
                ),
                "statement": "n > 0 and the family is historical-scope only",
                "lean_theorem": (
                    "AgadesPQC.IsogenyHistorical.Target."
                    "dimension_positive_historical_scope"
                ),
            }
            | _lean_source(
                "AgadesPQC.IsogenyHistorical.Target."
                "dimension_positive_historical_scope"
            )
        ]
    if family is TargetFamily.IMPLEMENTATION_SECURITY:
        return [
            {
                "invariant_id": "implementation_security.review_scope_declared",
                "statement": (
                    "implementation-security tasks declare a review-only scope"
                ),
                "lean_theorem": (
                    "AgadesPQC.ImplementationSecurity.Target."
                    "review_scope_declared"
                ),
            }
            | _lean_source(
                "AgadesPQC.ImplementationSecurity.Target.review_scope_declared"
            )
        ]
    return [
        {
            "invariant_id": f"{family.value.lower()}.family_shape_validated",
            "statement": "TargetSpec family-specific validator accepted the shape",
            "lean_theorem": "AgadesPQC.Generic.Target.family_shape_validated",
        }
        | _lean_source("AgadesPQC.Generic.Target.family_shape_validated")
    ]


def _lwe_lattice_invariants() -> list[dict[str, Any]]:
    return [
        {
            "invariant_id": "lattice.dimension_modulus_positive",
            "statement": "n > 0 and q > 1",
            "lean_theorem": "AgadesPQC.Lattice.Target.dimension_modulus_positive",
        }
        | _lean_source("AgadesPQC.Lattice.Target.dimension_modulus_positive"),
        {
            "invariant_id": "lattice.distributions_present",
            "statement": "secret and error distributions are present for LWE/MLWE",
            "lean_theorem": "AgadesPQC.Lattice.Target.distributions_present",
        }
        | _lean_source("AgadesPQC.Lattice.Target.distributions_present"),
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
    plan: AttackPlan,
    estimator_result_path: Path | None,
    *,
    root: Path | None = None,
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

    resolved_result_path = estimator_result_path
    if root is not None and not resolved_result_path.is_absolute():
        resolved_result_path = root / resolved_result_path
    raw = resolved_result_path.read_bytes()
    try:
        canonical_payload: Any = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            "attached estimator result must be a JSON EvaluatorResult"
        ) from exc
    evaluator_result = _validate_evaluator_result(canonical_payload)
    compatibility = _estimator_attack_plan_compatibility(plan, evaluator_result)
    if compatibility["compatible"] is not True:
        raise ValueError(
            "estimator result attack_type is incompatible with the bound AttackPlan"
        )
    return {
        "status": "attached_unreviewed",
        "path": estimator_result_path.as_posix(),
        "schema_contract": _evaluator_result_schema_contract(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "canonical_sha256": stable_sha256(canonical_payload),
        "parsed_result": _evaluator_result_summary(evaluator_result),
        "attack_plan_compatibility": compatibility,
        "claim_allowed": False,
        "notes": (
            "Estimator output is bound for reproducibility and reviewer "
            "inspection; it is not a reviewed cryptographic claim."
        ),
    }


def _proof_obligations(plan: AttackPlan) -> list[dict[str, Any]]:
    family = plan.target.family
    obligations: list[dict[str, Any]] = []
    if family is TargetFamily.LWE:
        obligations.extend(
            [
                _obligation(
                    "target.lwe.parameters.positive",
                    (
                        "Target parameters satisfy n > 0, q > 1, and m/k bounds "
                        "where present."
                    ),
                    "AgadesPQC.Lattice.Target.parameters_positive",
                    family=family,
                ),
                _obligation(
                    "target.lwe.distributions.present",
                    "Secret and error distributions are specified for LWE/MLWE.",
                    "AgadesPQC.Lattice.Target.distributions_present",
                    family=family,
                ),
            ]
        )
    if family is TargetFamily.MLWE:
        obligations.extend(
            [
                _obligation(
                    "target.mlwe.parameters.positive",
                    (
                        "MLWE target parameters satisfy n > 0, q > 1, "
                        "and module-rank bounds where present."
                    ),
                    "AgadesPQC.Lattice.Target.parameters_positive",
                    family=family,
                ),
                _obligation(
                    "target.mlwe.distributions.present",
                    "Secret and error distributions are specified for MLWE.",
                    "AgadesPQC.Lattice.Target.distributions_present",
                    family=family,
                ),
                _obligation(
                    "target.mlwe.module_rank.present",
                    "MLWE module rank k is positive.",
                    "AgadesPQC.Lattice.Target.module_rank_present",
                    family=family,
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
                family=family,
                operator_type="primal_usvp",
            )
        )
    if (
        family is TargetFamily.NTRU
        and plan.target.support_level is SupportLevel.SCHEMA_ONLY
    ):
        obligations.append(
            _obligation(
                "family.ntru.schema_only.no_estimate",
                "Schema-only NTRU plans must not emit cryptanalytic estimates.",
                "AgadesPQC.Lattice.Target.ntru_schema_only_no_estimate",
                family=family,
            )
        )
    if (
        family is TargetFamily.SIS
        and plan.target.support_level is SupportLevel.SCHEMA_ONLY
    ):
        obligations.append(
            _obligation(
                "family.sis.schema_only.no_estimate",
                "Schema-only SIS plans must not emit cryptanalytic estimates.",
                "AgadesPQC.Lattice.Target.sis_schema_only_no_estimate",
                family=family,
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
                family=family,
            )
        )
    if family is TargetFamily.MULTIVARIATE:
        obligations.append(
            _obligation(
                "family.multivariate.applicability_shape",
                (
                    "Multivariate AttackPlans require positive variables, "
                    "positive equations, and a declared finite field."
                ),
                "AgadesPQC.Multivariate.Target.applicability_shape",
                family=family,
            )
        )
    if family is TargetFamily.HASH_BASED:
        obligations.append(
            _obligation(
                "family.hash_based.bound_check_is_not_attack_claim",
                (
                    "Hash-based bound checks are applicability/routing checks, "
                    "not attack-success claims."
                ),
                "AgadesPQC.HashBased.Target.bound_check_is_not_attack_claim",
                family=family,
            )
        )
    if family is TargetFamily.ISOGENY_HISTORICAL:
        obligations.append(
            _obligation(
                "family.isogeny_historical.historical_only",
                (
                    "Historical isogeny tasks are toy/historical routing "
                    "checks and cannot describe current-standard break claims."
                ),
                "AgadesPQC.IsogenyHistorical.Target.historical_only",
                family=family,
            )
        )
    if family is TargetFamily.IMPLEMENTATION_SECURITY:
        obligations.append(
            _obligation(
                "family.implementation_security.no_conformance_claim",
                (
                    "Implementation-security toy checks do not establish "
                    "conformance, side-channel resistance, or security claims."
                ),
                "AgadesPQC.ImplementationSecurity.Target.no_conformance_claim",
                family=family,
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
            family=family,
        )
    )
    return obligations


def proof_obligation_type_rules() -> list[dict[str, Any]]:
    return [
        _proof_obligation_type_rule(kind)
        for kind in PROOF_OBLIGATION_TYPE_RULES
    ]


def _proof_obligation_type_rule(kind: str) -> dict[str, Any]:
    rule = PROOF_OBLIGATION_TYPE_RULES[kind]
    payload = {
        "schema_version": PROOF_OBLIGATION_TYPE_RULE_SCHEMA,
        "kind": kind,
        "statement": rule["statement"],
        "backend": "lean4",
        "lean_theorem": rule["lean_theorem"],
        **_lean_source(rule["lean_theorem"]),
    }
    return {
        **payload,
        "type_rule_sha256": stable_sha256(payload),
    }


def _obligation(
    obligation_id: str,
    statement: str,
    lean_theorem: str,
    *,
    family: TargetFamily,
    operator_type: str | None = None,
) -> dict[str, Any]:
    obligation_type = _obligation_type(
        obligation_id,
        family=family,
        operator_type=operator_type,
    )
    payload = {
        "obligation_id": obligation_id,
        "statement": statement,
        "backend": "lean4",
        "obligation_type": obligation_type,
        "type_rule": _proof_obligation_type_rule(obligation_type["kind"]),
        "lean_theorem": lean_theorem,
        **_lean_source(lean_theorem),
        "status": "pending_review",
    }
    return {
        **payload,
        "obligation_sha256": stable_sha256(payload),
    }


def _obligation_type(
    obligation_id: str,
    *,
    family: TargetFamily,
    operator_type: str | None = None,
) -> dict[str, Any]:
    kind = _obligation_type_kind(obligation_id)
    subject = _obligation_subject(
        kind,
        family=family,
        operator_type=operator_type,
    )
    return {
        "schema_version": PROOF_OBLIGATION_TYPE_SCHEMA,
        "kind": kind,
        "subject": subject,
        "claim_policy": dict(PROOF_OBLIGATION_CLAIM_POLICY),
    }


def _obligation_type_kind(obligation_id: str) -> str:
    if obligation_id.startswith("target."):
        return "target_invariant"
    if obligation_id.startswith("operator."):
        return "operator_precondition"
    if obligation_id.startswith("estimator."):
        return "estimator_claim_boundary"
    if obligation_id.startswith("family.") and ".schema_only." in obligation_id:
        return "schema_only_boundary"
    if obligation_id.startswith("family."):
        return "family_applicability_boundary"
    raise ValueError(f"Unsupported proof obligation id: {obligation_id}")


def _obligation_subject(
    kind: str,
    *,
    family: TargetFamily,
    operator_type: str | None,
) -> dict[str, str]:
    if kind == "target_invariant":
        return {
            "family": family.value,
            "scope": "target",
            "target_family": family.value,
        }
    if kind == "operator_precondition":
        return {
            "family": family.value,
            "operator": operator_type or "unknown",
            "scope": "operator",
        }
    if kind == "estimator_claim_boundary":
        return {
            "family": family.value,
            "scope": "estimator",
            "estimator_status": "no_security_claim_without_review",
        }
    if kind == "schema_only_boundary":
        return {
            "family": family.value,
            "scope": "schema_only_estimator_boundary",
            "support_level": SupportLevel.SCHEMA_ONLY.value,
        }
    if kind == "family_applicability_boundary":
        return {
            "family": family.value,
            "scope": "family_applicability",
            "target_family": family.value,
        }
    raise ValueError(f"Unsupported proof obligation type kind: {kind}")


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
        "proof_obligation_type_rules",
        "estimator_result_binding",
        "proof_obligations",
        "review",
        "formal_backend",
        "artifact_sha256",
    ):
        if key not in artifact:
            failures.append(f"Proof artifact is missing {key}.")


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
    if attack_plan.get("schema_contract") != _attack_plan_schema_contract():
        failures.append(
            "AttackPlan schema binding does not match current core schema."
        )
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
    if artifact.get("proof_obligation_type_rules") != proof_obligation_type_rules():
        failures.append("Proof obligation type rules do not match Lean bindings.")
    if artifact.get("proof_obligations") != _proof_obligations(plan):
        failures.append("Proof obligations do not match the AttackPlan.")
    _verify_lean_bindings(artifact, project_root, failures)


def _verify_obligation_hashes(
    artifact: dict[str, Any],
    project_root: Path,
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
                "obligation_type",
                "type_rule",
                "lean_theorem",
                "lean_source",
                "status",
            )
        }
        if obligation.get("backend") != "lean4":
            failures.append("Proof obligations must target lean4.")
        _verify_obligation_type(obligation, artifact, project_root, failures)
        if not obligation.get("lean_theorem"):
            failures.append("Proof obligations must bind a Lean theorem.")
        if obligation.get("obligation_sha256") != stable_sha256(payload):
            failures.append(
                f"Proof obligation hash mismatch: {obligation.get('obligation_id')}."
            )


def _attack_plan_schema_contract() -> dict[str, str]:
    return {
        "schema_version": ATTACK_PLAN_SCHEMA_CONTRACT_SCHEMA,
        "model": ATTACK_PLAN_SCHEMA_MODEL,
        "json_schema_sha256": stable_sha256(AttackPlan.model_json_schema()),
        "canonicalization": ATTACK_PLAN_CANONICALIZATION,
        "validation": ATTACK_PLAN_VALIDATION,
    }


def _evaluator_result_schema_contract() -> dict[str, str]:
    return {
        "schema_version": EVALUATOR_RESULT_SCHEMA_CONTRACT_SCHEMA,
        "model": EVALUATOR_RESULT_SCHEMA_MODEL,
        "json_schema_sha256": stable_sha256(EvaluatorResult.model_json_schema()),
        "canonicalization": ATTACK_PLAN_CANONICALIZATION,
        "validation": EVALUATOR_RESULT_VALIDATION,
    }


def _validate_evaluator_result(payload: Any) -> EvaluatorResult:
    return EvaluatorResult.model_validate(payload)


def _evaluator_result_summary(result: EvaluatorResult) -> dict[str, Any]:
    return {
        "schema_version": result.schema_version,
        "evaluator_name": result.evaluator_name,
        "evaluator_version": result.evaluator_version,
        "evaluator_commit": result.evaluator_commit,
        "evaluation_status": result.evaluation_status,
        "attack_type": result.attack_type,
        "claim_allowed": False,
    }


def _estimator_attack_plan_compatibility(
    plan: AttackPlan,
    result: EvaluatorResult,
) -> dict[str, Any]:
    return _estimator_attack_plan_compatibility_from_values(
        attack_plan_id=plan.attack_plan_id,
        target_family=plan.target.family.value,
        operator_types=[operator.type for operator in plan.operators],
        evaluator_attack_type=result.attack_type,
    )


def _estimator_attack_plan_compatibility_from_artifact(
    artifact: dict[str, Any],
    result: EvaluatorResult,
) -> dict[str, Any]:
    operator_types = [
        item.get("operator")
        for item in artifact.get("operator_semantics", [])
        if isinstance(item, dict) and isinstance(item.get("operator"), str)
    ]
    attack_plan = artifact.get("attack_plan", {})
    attack_plan_id = (
        attack_plan.get("id") if isinstance(attack_plan, dict) else None
    )
    family = artifact.get("family")
    return _estimator_attack_plan_compatibility_from_values(
        attack_plan_id=attack_plan_id if isinstance(attack_plan_id, str) else "",
        target_family=family if isinstance(family, str) else "",
        operator_types=operator_types,
        evaluator_attack_type=result.attack_type,
    )


def _estimator_attack_plan_compatibility_from_values(
    *,
    attack_plan_id: str,
    target_family: str,
    operator_types: list[str],
    evaluator_attack_type: str,
) -> dict[str, Any]:
    return {
        "attack_plan_id": attack_plan_id,
        "target_family": target_family,
        "operator_types": operator_types,
        "evaluator_attack_type": evaluator_attack_type,
        "compatible": _evaluator_attack_type_matches_operator(
            evaluator_attack_type,
            operator_types,
        ),
        "compatibility_rule": ESTIMATOR_ATTACK_TYPE_COMPATIBILITY_RULE,
    }


def _evaluator_attack_type_matches_operator(
    evaluator_attack_type: str,
    operator_types: list[str],
) -> bool:
    return any(
        evaluator_attack_type == operator_type
        or evaluator_attack_type.startswith(f"{operator_type}:")
        for operator_type in operator_types
    )


def _pending_review_evidence() -> dict[str, Any]:
    return {
        "schema_version": REVIEW_EVIDENCE_SCHEMA,
        "status": "not_attached",
        "required_for_statuses": ["reviewed", "rejected"],
        "covered_reviewer_roles": [],
        "claim_allowed": False,
        "notes": (
            "No reviewer attestation is attached; this artifact must remain "
            "pending_review."
        ),
    }


def _verify_type_rule(
    rule: dict[str, Any],
    project_root: Path,
    failures: list[str],
    *,
    label: str,
) -> None:
    if rule.get("schema_version") != PROOF_OBLIGATION_TYPE_RULE_SCHEMA:
        failures.append(f"Proof obligation type rule schema mismatch: {label}.")
    kind = rule.get("kind")
    if kind not in PROOF_OBLIGATION_TYPE_RULES:
        failures.append(f"Proof obligation type rule kind is unsupported: {label}.")
        return
    expected = PROOF_OBLIGATION_TYPE_RULES[kind]
    if rule.get("statement") != expected["statement"]:
        failures.append(f"Proof obligation type rule statement mismatch: {label}.")
    lean_theorem = rule.get("lean_theorem")
    if lean_theorem != expected["lean_theorem"]:
        failures.append(f"Proof obligation type rule theorem mismatch: {label}.")
    if rule.get("backend") != "lean4":
        failures.append(f"Proof obligation type rule must target Lean 4: {label}.")
    payload = {
        key: rule.get(key)
        for key in (
            "schema_version",
            "kind",
            "statement",
            "backend",
            "lean_theorem",
            "lean_source",
        )
    }
    if rule.get("type_rule_sha256") != stable_sha256(payload):
        failures.append(f"Proof obligation type rule hash mismatch: {label}.")
    source = rule.get("lean_source")
    if not isinstance(source, dict):
        failures.append(f"Proof obligation type rule source is missing: {label}.")
        return
    expected_path = LEAN_THEOREM_SOURCES.get(lean_theorem)
    if not isinstance(expected_path, str):
        failures.append(f"Proof obligation type rule source path mismatch: {label}.")
        return
    if source.get("path") != expected_path:
        failures.append(f"Proof obligation type rule source path mismatch: {label}.")
        return
    source_path = project_root / expected_path
    try:
        raw = source_path.read_bytes()
    except FileNotFoundError:
        failures.append(f"Proof obligation type rule source is missing: {label}.")
        return
    declaration = str(lean_theorem).rsplit(".", 1)[-1]
    if source.get("sha256") != hashlib.sha256(raw).hexdigest():
        failures.append(f"Proof obligation type rule source hash mismatch: {label}.")
    if source.get("declaration") != declaration:
        failures.append(
            f"Proof obligation type rule declaration mismatch: {label}."
        )
    if f"theorem {declaration}" not in raw.decode("utf-8"):
        failures.append(
            f"Proof obligation type rule theorem is missing from source: {label}."
        )


def _verify_obligation_type(
    obligation: dict[str, Any],
    artifact: dict[str, Any],
    project_root: Path,
    failures: list[str],
) -> None:
    obligation_id = obligation.get("obligation_id")
    obligation_type = obligation.get("obligation_type")
    if not isinstance(obligation_type, dict):
        failures.append(f"Proof obligation type is missing: {obligation_id}.")
        return
    if obligation_type.get("schema_version") != PROOF_OBLIGATION_TYPE_SCHEMA:
        failures.append(f"Proof obligation type schema mismatch: {obligation_id}.")
    kind = obligation_type.get("kind")
    if kind not in PROOF_OBLIGATION_TYPE_KINDS:
        failures.append(f"Proof obligation type kind is unsupported: {obligation_id}.")
    subject = obligation_type.get("subject")
    if not isinstance(subject, dict):
        failures.append(f"Proof obligation type subject is missing: {obligation_id}.")
    elif subject.get("family") != artifact.get("family"):
        failures.append(f"Proof obligation type family mismatch: {obligation_id}.")
    claim_policy = obligation_type.get("claim_policy")
    if not isinstance(claim_policy, dict):
        failures.append(
            f"Proof obligation claim policy is invalid: {obligation_id}."
        )
    else:
        if claim_policy.get("security_claim_allowed") is not False:
            failures.append(
                "Proof obligation type must forbid security claims: "
                f"{obligation_id}."
            )
        if claim_policy != PROOF_OBLIGATION_CLAIM_POLICY:
            failures.append(
                f"Proof obligation claim policy is invalid: {obligation_id}."
            )
    type_rule = obligation.get("type_rule")
    if not isinstance(type_rule, dict):
        failures.append(f"Proof obligation type rule is missing: {obligation_id}.")
        return
    if type_rule.get("kind") != kind:
        failures.append(f"Proof obligation type rule kind mismatch: {obligation_id}.")
    expected_rule = (
        _proof_obligation_type_rule(kind) if isinstance(kind, str) else None
    )
    if type_rule != expected_rule:
        failures.append(f"Proof obligation type rule mismatch: {obligation_id}.")
    _verify_type_rule(
        type_rule,
        project_root,
        failures,
        label=f"proof obligation {obligation_id}",
    )


def _verify_formal_backend(
    artifact: dict[str, Any],
    project_root: Path,
    failures: list[str],
) -> None:
    formal_backend = artifact.get("formal_backend")
    if not isinstance(formal_backend, dict):
        failures.append("Proof artifact formal_backend must be a JSON object.")
        return
    expected = _formal_backend_binding(project_root, failures=failures)
    if formal_backend != expected:
        failures.append("Proof artifact formal_backend is not in sync.")


def _formal_backend_binding(
    root: Path,
    *,
    failures: list[str] | None = None,
) -> dict[str, Any]:
    manifest_path = root / FORMAL_LEAN_BACKEND_PATH
    try:
        raw = manifest_path.read_bytes()
        manifest = json.loads(raw.decode("utf-8"))
    except FileNotFoundError:
        if failures is not None:
            failures.append(
                "Formal Lean backend manifest is missing: "
                f"{FORMAL_LEAN_BACKEND_PATH.as_posix()}."
            )
        manifest = {}
        raw = b""
    except json.JSONDecodeError as exc:
        if failures is not None:
            failures.append(
                "Formal Lean backend manifest is invalid JSON at line "
                f"{exc.lineno}."
            )
        manifest = {}
        raw = b""

    lean_project = manifest.get("lean_project", {})
    if not isinstance(lean_project, dict):
        lean_project = {}
    summary = manifest.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}

    return {
        "root": LEAN_BACKEND_ROOT.as_posix(),
        "toolchain": (LEAN_BACKEND_ROOT / "lean-toolchain").as_posix(),
        "toolchain_sha256": lean_project.get("toolchain_sha256"),
        "lakefile": (LEAN_BACKEND_ROOT / "lakefile.lean").as_posix(),
        "lakefile_sha256": lean_project.get("lakefile_sha256"),
        "lake_manifest": (LEAN_BACKEND_ROOT / "lake-manifest.json").as_posix(),
        "lake_manifest_sha256": lean_project.get("lake_manifest_sha256"),
        "entry_module": (LEAN_BACKEND_ROOT / "AgadesPQC.lean").as_posix(),
        "build_command": "lake build",
        "execution_status": "ci_build_gate_required",
        "backend_manifest": {
            "path": FORMAL_LEAN_BACKEND_PATH.as_posix(),
            "schema_version": manifest.get("schema_version"),
            "sha256": hashlib.sha256(raw).hexdigest() if raw else None,
            "manifest_sha256": manifest.get("manifest_sha256"),
            "source_modules": summary.get("source_modules"),
            "theorem_declarations": summary.get("theorem_declarations"),
            "ci_lean_build_gate": summary.get("ci_lean_build_gate"),
            "placeholder_failures": summary.get("placeholder_failures"),
        },
    }


def _verify_lean_bindings(
    artifact: dict[str, Any],
    project_root: Path,
    failures: list[str],
) -> None:
    entries = [
        *artifact.get("family_invariants", []),
        *artifact.get("proof_obligation_type_rules", []),
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
    except json.JSONDecodeError as exc:
        failures.append(
            f"Bound estimator result is invalid JSON at line {exc.lineno}."
        )
        return
    try:
        evaluator_result = _validate_evaluator_result(canonical_payload)
    except Exception as exc:  # noqa: BLE001
        failures.append(f"Bound estimator result is invalid: {exc}")
        return
    compatibility = _estimator_attack_plan_compatibility_from_artifact(
        artifact,
        evaluator_result,
    )
    if compatibility["compatible"] is not True:
        failures.append(
            "Estimator result attack_type is incompatible with bound AttackPlan."
        )
    if binding.get("schema_contract") != _evaluator_result_schema_contract():
        failures.append(
            "Estimator result schema binding does not match current core schema."
        )
    if binding.get("parsed_result") != _evaluator_result_summary(evaluator_result):
        failures.append("Estimator result parsed summary does not match bound file.")
    if binding.get("attack_plan_compatibility") != compatibility:
        failures.append(
            "Estimator result AttackPlan compatibility does not match bound files."
        )
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
    try:
        family = TargetFamily(artifact.get("family"))
    except ValueError:
        failures.append("Proof artifact family is unsupported for reviewer binding.")
        return
    if review.get("required_reviewers") != required_reviewers_for_family(family):
        failures.append("Proof artifact required reviewers are incorrect.")
    _verify_review_evidence(review, failures)
    _verify_reviewed_runtime_estimator_binding(artifact, failures)
    if "not PQC break claims" not in review.get("claim_boundary", ""):
        failures.append("Proof artifact must state the no-overclaim boundary.")


def _verify_reviewed_runtime_estimator_binding(
    artifact: dict[str, Any],
    failures: list[str],
) -> None:
    review = artifact.get("review", {})
    if not isinstance(review, dict) or review.get("status") == "pending_review":
        return
    estimator_model = artifact.get("estimator_model", {})
    if not isinstance(estimator_model, dict):
        return
    if estimator_model.get("status") != "result_binding_required_before_claim":
        return
    binding = artifact.get("estimator_result_binding", {})
    if not isinstance(binding, dict) or binding.get("status") != "attached_unreviewed":
        failures.append(
            "Reviewed runtime-estimator proof artifacts require an attached "
            "estimator result binding."
        )


def _verify_review_evidence(
    review: dict[str, Any],
    failures: list[str],
) -> None:
    evidence = review.get("evidence")
    if review.get("status") == "pending_review":
        if evidence != _pending_review_evidence():
            failures.append(
                "Pending proof artifacts must carry pending review evidence."
            )
        return
    if not isinstance(evidence, dict) or evidence.get("status") != "attached":
        failures.append(
            "Non-pending proof artifact review statuses require attached review "
            "evidence covering all required reviewers."
        )
        return
    required_reviewers = review.get("required_reviewers", [])
    covered_roles = evidence.get("covered_reviewer_roles", [])
    if sorted(covered_roles) != sorted(required_reviewers):
        failures.append(
            "Attached proof artifact review evidence must cover all required "
            "reviewer roles."
        )
