from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agades_pqc_gym.core.attack_plan import AttackOperator, AttackPlan
from agades_pqc_gym.core.family_adapter import ReproductionResult, ValidationFinding
from agades_pqc_gym.core.operators import PLACEHOLDER_OPERATORS
from agades_pqc_gym.core.target import SupportLevel, TargetFamily, TargetSpec
from agades_pqc_gym.evaluators.base import EstimatorResult
from agades_pqc_gym.families.fixtures import (
    is_scoped_public_fixture_path,
    resolve_public_fixture_path,
)
from agades_pqc_gym.families.hash_based.bound_estimator import (
    TOY_COLLISION_ASSUMPTION,
    TOY_COLLISION_BOUND_MODEL,
    TOY_FORS_AUTH_PATH_ASSUMPTION,
    TOY_FORS_AUTH_PATH_MODEL,
    TOY_HASH_MISUSE_ASSUMPTION,
    TOY_HASH_REUSED_SALT_MODEL,
    TOY_MERKLE_AUTH_PATH_ASSUMPTION,
    TOY_MERKLE_AUTH_PATH_MODEL,
    TOY_PREIMAGE_ASSUMPTION,
    TOY_PREIMAGE_BOUND_MODEL,
    TOY_SIGNATURE_CHAIN_ASSUMPTION,
    TOY_SIGNATURE_CHAIN_MODEL,
    TOY_SLH_DSA_HYPERTREE_ASSUMPTION,
    TOY_SLH_DSA_HYPERTREE_MODEL,
    ToyHashBoundEstimator,
)
from agades_pqc_gym.families.hash_based.collision_fixture import (
    verify_toy_collision_fixture,
)
from agades_pqc_gym.families.hash_based.misuse_fixture import (
    verify_toy_hash_misuse_fixture,
)
from agades_pqc_gym.families.hash_based.preimage_solver import (
    solve_toy_preimage_fixture,
)
from agades_pqc_gym.families.hash_based.signature_fixture import (
    verify_toy_fors_auth_path_fixture,
    verify_toy_merkle_auth_path_fixture,
    verify_toy_signature_chain_fixture,
    verify_toy_slh_dsa_hypertree_fixture,
)
from agades_pqc_gym.families.schema_only import (
    SCHEMA_ONLY_ASSUMPTION,
    SchemaOnlyFamilyAdapter,
)

REVIEWED_HASH_FUNCTIONS = frozenset({"SHA2", "SHA3", "SHAKE128", "SHAKE256"})
_MAX_TOY_DIGEST_BITS = 64
HASH_BASED_INSTANCE_REPRODUCTION_SCORE = 0.4
ROOT = Path(__file__).resolve().parents[4]
PACKAGE_FIXTURES = Path(__file__).resolve().parent / "fixtures"
_PREIMAGE_FIXTURE_ROOT_PARTS = ("benchmarks", "hash_based_toy_bound", "fixtures")
_SIGNATURE_FIXTURE_ROOT_PARTS = (
    "benchmarks",
    "hash_based_toy_signature",
    "fixtures",
)
_MISUSE_FIXTURE_ROOT_PARTS = ("benchmarks", "hash_based_toy_misuse", "fixtures")


@dataclass(frozen=True)
class HashBasedFamilyAdapter:
    family: TargetFamily = TargetFamily.HASH_BASED
    support_level: str = "toy_evaluator"
    estimator_name: str = ToyHashBoundEstimator.estimator_name

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "_schema_only",
            SchemaOnlyFamilyAdapter(
                family=TargetFamily.HASH_BASED,
                estimator_name="hash-based-placeholder-estimator",
            ),
        )
        object.__setattr__(self, "_estimator", ToyHashBoundEstimator())

    def validate_target(self, target: TargetSpec) -> list[ValidationFinding]:
        findings = _validate_hash_shape(target)
        if target.family is not TargetFamily.HASH_BASED:
            return findings
        if target.support_level is SupportLevel.SCHEMA_ONLY:
            return [*findings, *self._schema_only.validate_target(target)]
        if target.support_level is not SupportLevel.IMPLEMENTED:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="hash_based_support_level_unknown",
                    message=(
                        "HASH_BASED targets must be schema_only or implemented "
                        "for the reviewed toy bound evaluator"
                    ),
                )
            )
            return findings

        if not target.name.startswith("toy_"):
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="hash_based_toy_target_required",
                    message=(
                        "HASH_BASED implemented evaluator is limited to toy_ "
                        "hash-bound targets"
                    ),
                )
            )
        if target.n is None:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="hash_based_digest_bits_required",
                    message="HASH_BASED implemented toy evaluator requires n",
                )
            )
        elif target.n > _MAX_TOY_DIGEST_BITS:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="hash_based_toy_digest_limit",
                    message=(
                        "HASH_BASED implemented toy evaluator requires "
                        f"n <= {_MAX_TOY_DIGEST_BITS}"
                    ),
                )
            )
        return findings

    def validate_plan(self, plan: AttackPlan) -> list[ValidationFinding]:
        if plan.target.support_level is SupportLevel.SCHEMA_ONLY:
            return self._schema_only.validate_plan(plan)

        findings: list[ValidationFinding] = []
        for operator in plan.operators:
            if operator.type == "security_bound_check":
                findings.extend(_validate_security_bound_operator(operator))
            elif operator.type == "hash_signature_verification":
                findings.extend(_validate_signature_operator(operator))
            elif operator.type == "misuse_check":
                findings.extend(_validate_misuse_operator(operator))
            else:
                findings.append(
                    ValidationFinding(
                        severity="error",
                        code="hash_based_unreviewed_operator",
                        message=(
                            "HASH_BASED implemented evaluator supports only "
                            "security_bound_check, hash_signature_verification, "
                            "or misuse_check"
                        ),
                    )
                )
            if SCHEMA_ONLY_ASSUMPTION in operator.assumptions:
                findings.append(
                    ValidationFinding(
                        severity="error",
                        code="hash_based_schema_only_assumption_on_implemented_plan",
                        message=(
                            "HASH_BASED implemented toy plans must not use "
                            f"{SCHEMA_ONLY_ASSUMPTION}"
                        ),
                    )
                )
        if (
            plan.constraints.require_reproducibility_on_downscaled_instances
            and plan.constraints.downscaled_reproduction_fixture is None
        ):
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="hash_based_reproduction_fixture_required",
                    message=(
                        "HASH_BASED toy reproduction requires an explicit "
                        "public hash-bound or signature fixture"
                    ),
                )
            )
        if plan.constraints.downscaled_reproduction_fixture is not None:
            fixture_path = Path(plan.constraints.downscaled_reproduction_fixture)
            if _is_misuse_plan(plan):
                fixture_is_scoped = _is_scoped_misuse_fixture_path(fixture_path)
                fixture_scope = "benchmarks/hash_based_toy_misuse/fixtures/"
            elif _is_signature_plan(plan):
                fixture_is_scoped = _is_scoped_signature_fixture_path(fixture_path)
                fixture_scope = "benchmarks/hash_based_toy_signature/fixtures/"
            else:
                fixture_is_scoped = _is_scoped_preimage_fixture_path(fixture_path)
                fixture_scope = "benchmarks/hash_based_toy_bound/fixtures/"
            if not fixture_is_scoped:
                findings.append(
                    ValidationFinding(
                        severity="error",
                        code="hash_based_reproduction_fixture_scope",
                        message=(
                            "HASH_BASED reproduction fixtures must be relative "
                            f"paths under {fixture_scope}"
                        ),
                    )
                )
        if any(
            claim is not None
            for claim in (
                plan.claims.estimated_time_bits,
                plan.claims.estimated_memory_bits,
                plan.claims.success_probability,
            )
        ):
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="hash_based_pre_evaluation_claims_not_allowed",
                    message=(
                        "HASH_BASED toy plans must not include cryptanalytic "
                        "estimate claims"
                    ),
                )
            )
        return findings

    def supported_operators(self) -> set[str]:
        return set(PLACEHOLDER_OPERATORS[TargetFamily.HASH_BASED])

    def estimate(self, plan: AttackPlan) -> EstimatorResult:
        if plan.target.support_level is SupportLevel.SCHEMA_ONLY:
            return self._schema_only.estimate(plan)
        return self._estimator.estimate(plan)

    def reproduce_downscaled(self, plan: AttackPlan) -> ReproductionResult | None:
        if not plan.constraints.require_reproducibility_on_downscaled_instances:
            return None

        fixture_path_value = plan.constraints.downscaled_reproduction_fixture
        if not fixture_path_value:
            return ReproductionResult(
                attempted=False,
                status="not_applicable",
                success=False,
                warnings=[
                    "HASH_BASED toy reproduction requires an explicit public "
                    "hash-bound or signature fixture."
                ],
            )

        fixture_path, fixture_warnings = _resolve_fixture_path(fixture_path_value)
        if fixture_path is None:
            return ReproductionResult(
                attempted=False,
                status="not_applicable",
                success=False,
                warnings=fixture_warnings,
            )
        if _is_scoped_signature_fixture_path(Path(fixture_path_value)):
            return _reproduce_signature_chain(plan, fixture_path)
        if _is_scoped_misuse_fixture_path(Path(fixture_path_value)):
            return _reproduce_misuse(plan, fixture_path)
        if _is_collision_bound_plan(plan):
            return _reproduce_collision(plan, fixture_path)

        try:
            solution = solve_toy_preimage_fixture(fixture_path)
        except (OSError, ValueError) as exc:
            return ReproductionResult(
                attempted=True,
                status="failed",
                success=False,
                warnings=[
                    f"HASH_BASED toy preimage fixture could not be solved: {exc}"
                ],
            )

        if (
            solution.solved
            and solution.target_name == plan.target.name
            and solution.digest_bits == plan.target.n
            and solution.hash_function == plan.target.hash_function
            and solution.public
            and not solution.security_claim
        ):
            return ReproductionResult(
                attempted=True,
                status="instance_solved",
                success=True,
                score=HASH_BASED_INSTANCE_REPRODUCTION_SCORE,
                warnings=[
                    "Solved a public toy SHAKE256 preimage fixture with "
                    "bounded exhaustive search; this is reproducibility "
                    "plumbing, not a security claim."
                ],
            )
        return ReproductionResult(
            attempted=True,
            status="failed",
            success=False,
            warnings=[
                "HASH_BASED toy preimage fixture did not produce the expected "
                "public target solution."
            ],
        )


def _validate_security_bound_operator(
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    bound_model = operator.params.get("bound_model")
    if bound_model not in {TOY_PREIMAGE_BOUND_MODEL, TOY_COLLISION_BOUND_MODEL}:
        findings.append(
            ValidationFinding(
                severity="error",
                code="hash_based_unreviewed_bound_model",
                message=(
                    "HASH_BASED security_bound_check supports only "
                    f"{TOY_PREIMAGE_BOUND_MODEL} or {TOY_COLLISION_BOUND_MODEL}"
                ),
            )
        )
        return findings
    if (
        bound_model == TOY_PREIMAGE_BOUND_MODEL
        and TOY_PREIMAGE_ASSUMPTION not in operator.assumptions
    ):
        findings.append(
            ValidationFinding(
                severity="error",
                code="hash_based_toy_bound_assumption_required",
                message=(
                    "HASH_BASED toy_preimage_bound plans must include "
                    f"{TOY_PREIMAGE_ASSUMPTION}"
                ),
            )
        )
    if (
        bound_model == TOY_COLLISION_BOUND_MODEL
        and TOY_COLLISION_ASSUMPTION not in operator.assumptions
    ):
        findings.append(
            ValidationFinding(
                severity="error",
                code="hash_based_collision_bound_assumption_required",
                message=(
                    "HASH_BASED toy_collision_bound plans must include "
                    f"{TOY_COLLISION_ASSUMPTION}"
                ),
            )
        )
    return findings


def _validate_signature_operator(operator: AttackOperator) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    signature_model = operator.params.get("signature_model")
    if signature_model not in {
        TOY_SIGNATURE_CHAIN_MODEL,
        TOY_MERKLE_AUTH_PATH_MODEL,
        TOY_FORS_AUTH_PATH_MODEL,
        TOY_SLH_DSA_HYPERTREE_MODEL,
    }:
        findings.append(
            ValidationFinding(
                severity="error",
                code="hash_based_unreviewed_signature_model",
                message=(
                    "HASH_BASED hash_signature_verification supports only "
                    f"{TOY_SIGNATURE_CHAIN_MODEL}, {TOY_MERKLE_AUTH_PATH_MODEL}, "
                    f"{TOY_FORS_AUTH_PATH_MODEL}, or {TOY_SLH_DSA_HYPERTREE_MODEL}"
                ),
            )
        )
        return findings
    if signature_model == TOY_SIGNATURE_CHAIN_MODEL:
        findings.extend(_validate_signature_chain_operator(operator))
    if signature_model == TOY_MERKLE_AUTH_PATH_MODEL:
        findings.extend(_validate_merkle_auth_path_operator(operator))
    if signature_model == TOY_FORS_AUTH_PATH_MODEL:
        findings.extend(_validate_fors_auth_path_operator(operator))
    if signature_model == TOY_SLH_DSA_HYPERTREE_MODEL:
        findings.extend(_validate_slh_dsa_hypertree_operator(operator))
    return findings


def _validate_misuse_operator(operator: AttackOperator) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    fixture = operator.params.get("fixture")
    if fixture != TOY_HASH_REUSED_SALT_MODEL:
        findings.append(
            ValidationFinding(
                severity="error",
                code="hash_based_unreviewed_misuse_fixture",
                message=(
                    "HASH_BASED misuse_check supports only "
                    f"{TOY_HASH_REUSED_SALT_MODEL}"
                ),
            )
        )
        return findings
    if TOY_HASH_MISUSE_ASSUMPTION not in operator.assumptions:
        findings.append(
            ValidationFinding(
                severity="error",
                code="hash_based_misuse_assumption_required",
                message=(
                    "HASH_BASED toy_hash_reused_salt plans must include "
                    f"{TOY_HASH_MISUSE_ASSUMPTION}"
                ),
            )
        )
    for param_name in ("record_count", "expected_reuse_groups", "salt_bytes"):
        if not _is_positive_int(operator.params.get(param_name)):
            findings.append(
                ValidationFinding(
                    severity="error",
                    code=f"hash_based_misuse_{param_name}_required",
                    message=(
                        "HASH_BASED toy_hash_reused_salt requires positive "
                        f"integer {param_name}"
                    ),
                )
            )
    return findings


def _validate_signature_chain_operator(
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    if TOY_SIGNATURE_CHAIN_ASSUMPTION not in operator.assumptions:
        findings.append(
            ValidationFinding(
                severity="error",
                code="hash_based_signature_chain_assumption_required",
                message=(
                    "HASH_BASED toy_wots_chain_verify plans must include "
                    f"{TOY_SIGNATURE_CHAIN_ASSUMPTION}"
                ),
            )
        )
    for param_name in ("chain_count", "max_chain_steps"):
        if not _is_positive_int(operator.params.get(param_name)):
            findings.append(
                ValidationFinding(
                    severity="error",
                    code=f"hash_based_signature_{param_name}_required",
                    message=(
                        "HASH_BASED toy_wots_chain_verify requires positive "
                        f"integer {param_name}"
                    ),
                )
            )
    return findings


def _validate_merkle_auth_path_operator(
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    if TOY_MERKLE_AUTH_PATH_ASSUMPTION not in operator.assumptions:
        findings.append(
            ValidationFinding(
                severity="error",
                code="hash_based_merkle_auth_path_assumption_required",
                message=(
                    "HASH_BASED toy_merkle_auth_path_verify plans must "
                    f"include {TOY_MERKLE_AUTH_PATH_ASSUMPTION}"
                ),
            )
        )
    tree_height = operator.params.get("tree_height")
    leaf_index = operator.params.get("leaf_index")
    if not _is_positive_int(tree_height):
        findings.append(
            ValidationFinding(
                severity="error",
                code="hash_based_merkle_tree_height_required",
                message=(
                    "HASH_BASED toy_merkle_auth_path_verify requires "
                    "positive integer tree_height"
                ),
            )
        )
    if not _is_non_negative_int(leaf_index):
        findings.append(
            ValidationFinding(
                severity="error",
                code="hash_based_merkle_leaf_index_required",
                message=(
                    "HASH_BASED toy_merkle_auth_path_verify requires "
                    "non-negative integer leaf_index"
                ),
            )
        )
    if _is_positive_int(tree_height) and _is_non_negative_int(leaf_index):
        if tree_height > 16:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="hash_based_merkle_tree_height_limit",
                    message=(
                        "HASH_BASED toy_merkle_auth_path_verify requires "
                        "tree_height <= 16"
                    ),
                )
            )
        if leaf_index >= 2**tree_height:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="hash_based_merkle_leaf_index_bounds",
                    message=(
                        "HASH_BASED toy_merkle_auth_path_verify requires "
                        "leaf_index < 2**tree_height"
                    ),
                )
            )
    return findings


def _validate_fors_auth_path_operator(
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    if TOY_FORS_AUTH_PATH_ASSUMPTION not in operator.assumptions:
        findings.append(
            ValidationFinding(
                severity="error",
                code="hash_based_fors_auth_path_assumption_required",
                message=(
                    "HASH_BASED toy_fors_auth_path_verify plans must "
                    f"include {TOY_FORS_AUTH_PATH_ASSUMPTION}"
                ),
            )
        )
    tree_count = operator.params.get("tree_count")
    tree_height = operator.params.get("tree_height")
    selected_indices = operator.params.get("selected_indices")
    if not _is_positive_int(tree_count):
        findings.append(
            ValidationFinding(
                severity="error",
                code="hash_based_fors_tree_count_required",
                message=(
                    "HASH_BASED toy_fors_auth_path_verify requires "
                    "positive integer tree_count"
                ),
            )
        )
    if not _is_positive_int(tree_height):
        findings.append(
            ValidationFinding(
                severity="error",
                code="hash_based_fors_tree_height_required",
                message=(
                    "HASH_BASED toy_fors_auth_path_verify requires "
                    "positive integer tree_height"
                ),
            )
        )
    if not isinstance(selected_indices, list) or any(
        not _is_non_negative_int(index) for index in selected_indices
    ):
        findings.append(
            ValidationFinding(
                severity="error",
                code="hash_based_fors_selected_indices_required",
                message=(
                    "HASH_BASED toy_fors_auth_path_verify requires "
                    "non-negative integer selected_indices"
                ),
            )
        )
        return findings
    if _is_positive_int(tree_count) and len(selected_indices) != tree_count:
        findings.append(
            ValidationFinding(
                severity="error",
                code="hash_based_fors_selected_indices_count",
                message=(
                    "HASH_BASED toy_fors_auth_path_verify requires "
                    "selected_indices length == tree_count"
                ),
            )
        )
    if _is_positive_int(tree_count) and tree_count > 16:
        findings.append(
            ValidationFinding(
                severity="error",
                code="hash_based_fors_tree_count_limit",
                message=(
                    "HASH_BASED toy_fors_auth_path_verify requires tree_count <= 16"
                ),
            )
        )
    if _is_positive_int(tree_height):
        if tree_height > 16:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="hash_based_fors_tree_height_limit",
                    message=(
                        "HASH_BASED toy_fors_auth_path_verify requires "
                        "tree_height <= 16"
                    ),
                )
            )
        if any(index >= 2**tree_height for index in selected_indices):
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="hash_based_fors_selected_indices_bounds",
                    message=(
                        "HASH_BASED toy_fors_auth_path_verify requires each "
                        "selected index < 2**tree_height"
                    ),
                )
            )
    return findings


def _validate_slh_dsa_hypertree_operator(
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    if TOY_SLH_DSA_HYPERTREE_ASSUMPTION not in operator.assumptions:
        findings.append(
            ValidationFinding(
                severity="error",
                code="hash_based_slh_dsa_hypertree_assumption_required",
                message=(
                    "HASH_BASED toy_slh_dsa_hypertree_verify plans must "
                    f"include {TOY_SLH_DSA_HYPERTREE_ASSUMPTION}"
                ),
            )
        )

    fors_tree_count = operator.params.get("fors_tree_count")
    fors_tree_height = operator.params.get("fors_tree_height")
    fors_selected_indices = operator.params.get("fors_selected_indices")
    wots_chain_count = operator.params.get("wots_chain_count")
    wots_max_chain_steps = operator.params.get("wots_max_chain_steps")
    hypertree_height = operator.params.get("hypertree_height")
    hypertree_leaf_index = operator.params.get("hypertree_leaf_index")

    for name, value in (
        ("fors_tree_count", fors_tree_count),
        ("fors_tree_height", fors_tree_height),
        ("wots_chain_count", wots_chain_count),
        ("wots_max_chain_steps", wots_max_chain_steps),
        ("hypertree_height", hypertree_height),
    ):
        if not _is_positive_int(value):
            findings.append(
                ValidationFinding(
                    severity="error",
                    code=f"hash_based_slh_dsa_{name}_required",
                    message=(
                        "HASH_BASED toy_slh_dsa_hypertree_verify requires "
                        f"positive integer {name}"
                    ),
                )
            )

    if not _is_non_negative_int(hypertree_leaf_index):
        findings.append(
            ValidationFinding(
                severity="error",
                code="hash_based_slh_dsa_hypertree_leaf_index_required",
                message=(
                    "HASH_BASED toy_slh_dsa_hypertree_verify requires "
                    "non-negative integer hypertree_leaf_index"
                ),
            )
        )

    if not isinstance(fors_selected_indices, list) or any(
        not _is_non_negative_int(index) for index in fors_selected_indices
    ):
        findings.append(
            ValidationFinding(
                severity="error",
                code="hash_based_slh_dsa_selected_indices_required",
                message=(
                    "HASH_BASED toy_slh_dsa_hypertree_verify requires "
                    "non-negative integer fors_selected_indices"
                ),
            )
        )
        return findings

    if _is_positive_int(fors_tree_count):
        if len(fors_selected_indices) != fors_tree_count:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="hash_based_slh_dsa_selected_indices_count",
                    message=(
                        "HASH_BASED toy_slh_dsa_hypertree_verify requires "
                        "fors_selected_indices length == fors_tree_count"
                    ),
                )
            )
        if fors_tree_count > 16:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="hash_based_slh_dsa_fors_tree_count_limit",
                    message=(
                        "HASH_BASED toy_slh_dsa_hypertree_verify requires "
                        "fors_tree_count <= 16"
                    ),
                )
            )

    if _is_positive_int(fors_tree_height):
        if fors_tree_height > 16:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="hash_based_slh_dsa_fors_tree_height_limit",
                    message=(
                        "HASH_BASED toy_slh_dsa_hypertree_verify requires "
                        "fors_tree_height <= 16"
                    ),
                )
            )
        if any(index >= 2**fors_tree_height for index in fors_selected_indices):
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="hash_based_slh_dsa_selected_indices_bounds",
                    message=(
                        "HASH_BASED toy_slh_dsa_hypertree_verify requires "
                        "each selected index < 2**fors_tree_height"
                    ),
                )
            )

    if _is_positive_int(wots_chain_count) and wots_chain_count > 16:
        findings.append(
            ValidationFinding(
                severity="error",
                code="hash_based_slh_dsa_wots_chain_count_limit",
                message=(
                    "HASH_BASED toy_slh_dsa_hypertree_verify requires "
                    "wots_chain_count <= 16"
                ),
            )
        )
    if _is_positive_int(wots_max_chain_steps) and wots_max_chain_steps > 64:
        findings.append(
            ValidationFinding(
                severity="error",
                code="hash_based_slh_dsa_wots_max_chain_steps_limit",
                message=(
                    "HASH_BASED toy_slh_dsa_hypertree_verify requires "
                    "wots_max_chain_steps <= 64"
                ),
            )
        )
    if _is_positive_int(hypertree_height):
        if hypertree_height > 16:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="hash_based_slh_dsa_hypertree_height_limit",
                    message=(
                        "HASH_BASED toy_slh_dsa_hypertree_verify requires "
                        "hypertree_height <= 16"
                    ),
                )
            )
        if (
            _is_non_negative_int(hypertree_leaf_index)
            and hypertree_leaf_index >= 2**hypertree_height
        ):
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="hash_based_slh_dsa_hypertree_leaf_index_bounds",
                    message=(
                        "HASH_BASED toy_slh_dsa_hypertree_verify requires "
                        "hypertree_leaf_index < 2**hypertree_height"
                    ),
                )
            )
    return findings


def _is_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_signature_plan(plan: AttackPlan) -> bool:
    return _signature_operator(plan) is not None


def _is_misuse_plan(plan: AttackPlan) -> bool:
    return any(operator.type == "misuse_check" for operator in plan.operators)


def _misuse_operator(plan: AttackPlan) -> AttackOperator | None:
    for operator in plan.operators:
        if operator.type == "misuse_check":
            return operator
    return None


def _signature_operator(plan: AttackPlan) -> AttackOperator | None:
    for operator in plan.operators:
        if operator.type == "hash_signature_verification":
            return operator
    return None


def _is_collision_bound_plan(plan: AttackPlan) -> bool:
    return any(
        operator.type == "security_bound_check"
        and operator.params.get("bound_model") == TOY_COLLISION_BOUND_MODEL
        for operator in plan.operators
    )


def _validate_hash_shape(target: TargetSpec) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    if target.family is not TargetFamily.HASH_BASED:
        findings.append(
            ValidationFinding(
                severity="error",
                code="family_adapter_mismatch",
                message=(
                    f"HASH_BASED adapter cannot validate {target.family.value} targets"
                ),
            )
        )
        return findings

    if (
        target.hash_function is not None
        and target.hash_function not in REVIEWED_HASH_FUNCTIONS
    ):
        findings.append(
            ValidationFinding(
                severity="error",
                code="hash_based_unreviewed_hash",
                message=(
                    "HASH_BASED hash_function must be one of "
                    f"{sorted(REVIEWED_HASH_FUNCTIONS)}"
                ),
            )
        )
    return findings


def _reproduce_collision(
    plan: AttackPlan,
    fixture_path: Path,
) -> ReproductionResult:
    try:
        result = verify_toy_collision_fixture(fixture_path)
    except (OSError, ValueError) as exc:
        return ReproductionResult(
            attempted=True,
            status="failed",
            success=False,
            warnings=[
                "HASH_BASED toy collision fixture could not be verified: "
                f"{exc}"
            ],
        )

    if (
        result.verified
        and result.target_name == plan.target.name
        and result.digest_bits == plan.target.n
        and result.hash_function == plan.target.hash_function
        and result.public
        and not result.security_claim
    ):
        return ReproductionResult(
            attempted=True,
            status="instance_solved",
            success=True,
            score=HASH_BASED_INSTANCE_REPRODUCTION_SCORE,
            warnings=[
                "Verified a public toy SHAKE256 truncated-collision fixture; "
                "this is reproducibility plumbing, not collision-finding "
                "evidence and not a security claim."
            ],
        )
    return ReproductionResult(
        attempted=True,
        status="failed",
        success=False,
        warnings=[
            "HASH_BASED toy collision fixture did not produce the expected "
            "public target verification."
        ],
    )


def _reproduce_signature_chain(
    plan: AttackPlan,
    fixture_path: Path,
) -> ReproductionResult:
    signature_operator = _signature_operator(plan)
    if signature_operator is None:
        return ReproductionResult(
            attempted=True,
            status="failed",
            success=False,
            warnings=[
                "HASH_BASED signature reproduction requires a "
                "hash_signature_verification operator."
            ],
        )

    signature_model = signature_operator.params.get("signature_model")
    if signature_model == TOY_MERKLE_AUTH_PATH_MODEL:
        return _reproduce_merkle_auth_path(plan, fixture_path)
    if signature_model == TOY_FORS_AUTH_PATH_MODEL:
        return _reproduce_fors_auth_path(plan, fixture_path)
    if signature_model == TOY_SLH_DSA_HYPERTREE_MODEL:
        return _reproduce_slh_dsa_hypertree(plan, fixture_path)

    try:
        result = verify_toy_signature_chain_fixture(fixture_path)
    except (OSError, ValueError) as exc:
        return ReproductionResult(
            attempted=True,
            status="failed",
            success=False,
            warnings=[
                "HASH_BASED toy signature fixture could not be verified: "
                f"{exc}"
            ],
        )

    if (
        result.verified
        and result.target_name == plan.target.name
        and result.digest_bits == plan.target.n
        and result.hash_function == plan.target.hash_function
        and result.public
        and not result.security_claim
    ):
        return ReproductionResult(
            attempted=True,
            status="instance_solved",
            success=True,
            score=HASH_BASED_INSTANCE_REPRODUCTION_SCORE,
            warnings=[
                "Verified a public toy SHAKE256 hash-signature chain fixture; "
                "this is reproducibility plumbing, not a security claim."
            ],
        )
    return ReproductionResult(
        attempted=True,
        status="failed",
        success=False,
        warnings=[
            "HASH_BASED toy signature fixture did not produce the expected "
            "public target verification."
        ],
    )


def _reproduce_merkle_auth_path(
    plan: AttackPlan,
    fixture_path: Path,
) -> ReproductionResult:
    try:
        result = verify_toy_merkle_auth_path_fixture(fixture_path)
    except (OSError, ValueError) as exc:
        return ReproductionResult(
            attempted=True,
            status="failed",
            success=False,
            warnings=[
                "HASH_BASED toy Merkle auth-path fixture could not be "
                f"verified: {exc}"
            ],
        )

    if (
        result.verified
        and result.target_name == plan.target.name
        and result.digest_bits == plan.target.n
        and result.hash_function == plan.target.hash_function
        and result.public
        and not result.security_claim
    ):
        return ReproductionResult(
            attempted=True,
            status="instance_solved",
            success=True,
            score=HASH_BASED_INSTANCE_REPRODUCTION_SCORE,
            warnings=[
                "Verified a public toy SHAKE256 Merkle auth-path fixture; "
                "this is reproducibility plumbing, not a signature security "
                "claim and not a security claim."
            ],
        )
    return ReproductionResult(
        attempted=True,
        status="failed",
        success=False,
        warnings=[
            "HASH_BASED toy Merkle auth-path fixture did not produce the "
            "expected public target verification."
        ],
    )


def _reproduce_fors_auth_path(
    plan: AttackPlan,
    fixture_path: Path,
) -> ReproductionResult:
    signature_operator = _signature_operator(plan)
    if signature_operator is None:
        return ReproductionResult(
            attempted=True,
            status="failed",
            success=False,
            warnings=[
                "HASH_BASED FORS reproduction requires a "
                "hash_signature_verification operator."
            ],
        )
    try:
        result = verify_toy_fors_auth_path_fixture(fixture_path)
    except (OSError, ValueError) as exc:
        return ReproductionResult(
            attempted=True,
            status="failed",
            success=False,
            warnings=[
                "HASH_BASED toy FORS auth-path fixture could not be "
                f"verified: {exc}"
            ],
        )

    if (
        result.verified
        and result.target_name == plan.target.name
        and result.digest_bits == plan.target.n
        and result.hash_function == plan.target.hash_function
        and result.public
        and not result.security_claim
        and result.tree_count == signature_operator.params.get("tree_count")
        and result.tree_height == signature_operator.params.get("tree_height")
        and result.selected_indices
        == signature_operator.params.get("selected_indices")
    ):
        return ReproductionResult(
            attempted=True,
            status="instance_solved",
            success=True,
            score=HASH_BASED_INSTANCE_REPRODUCTION_SCORE,
            warnings=[
                "Verified a public toy SHAKE256 FORS auth-path fixture; this "
                "is reproducibility plumbing, not an SLH-DSA result and not a "
                "security claim."
            ],
        )
    return ReproductionResult(
        attempted=True,
        status="failed",
        success=False,
        warnings=[
            "HASH_BASED toy FORS auth-path fixture did not produce the "
            "expected public target verification."
        ],
    )


def _reproduce_slh_dsa_hypertree(
    plan: AttackPlan,
    fixture_path: Path,
) -> ReproductionResult:
    signature_operator = _signature_operator(plan)
    if signature_operator is None:
        return ReproductionResult(
            attempted=True,
            status="failed",
            success=False,
            warnings=[
                "HASH_BASED SLH-DSA-like reproduction requires a "
                "hash_signature_verification operator."
            ],
        )
    try:
        result = verify_toy_slh_dsa_hypertree_fixture(fixture_path)
    except (OSError, ValueError) as exc:
        return ReproductionResult(
            attempted=True,
            status="failed",
            success=False,
            warnings=[
                "HASH_BASED toy SLH-DSA-like hypertree fixture could not be "
                f"verified: {exc}"
            ],
        )

    if (
        result.verified
        and result.target_name == plan.target.name
        and result.digest_bits == plan.target.n
        and result.hash_function == plan.target.hash_function
        and result.public
        and not result.security_claim
        and result.fors_tree_count
        == signature_operator.params.get("fors_tree_count")
        and result.fors_tree_height
        == signature_operator.params.get("fors_tree_height")
        and result.fors_selected_indices
        == signature_operator.params.get("fors_selected_indices")
        and result.wots_chain_count
        == signature_operator.params.get("wots_chain_count")
        and result.wots_max_chain_steps
        == signature_operator.params.get("wots_max_chain_steps")
        and result.hypertree_height
        == signature_operator.params.get("hypertree_height")
        and result.hypertree_leaf_index
        == signature_operator.params.get("hypertree_leaf_index")
    ):
        return ReproductionResult(
            attempted=True,
            status="instance_solved",
            success=True,
            score=HASH_BASED_INSTANCE_REPRODUCTION_SCORE,
            warnings=[
                "Verified a public toy SHAKE256 SLH-DSA-like hypertree "
                "fixture; this is reproducibility plumbing, not an SLH-DSA "
                "result and not a security claim."
            ],
        )
    return ReproductionResult(
        attempted=True,
        status="failed",
        success=False,
        warnings=[
            "HASH_BASED toy SLH-DSA-like hypertree fixture did not produce "
            "the expected public target verification."
        ],
    )


def _reproduce_misuse(
    plan: AttackPlan,
    fixture_path: Path,
) -> ReproductionResult:
    operator = _misuse_operator(plan)
    if operator is None:
        return ReproductionResult(
            attempted=True,
            status="failed",
            success=False,
            warnings=["HASH_BASED toy misuse reproduction requires misuse_check."],
        )
    try:
        result = verify_toy_hash_misuse_fixture(fixture_path)
    except (OSError, ValueError) as exc:
        return ReproductionResult(
            attempted=True,
            status="failed",
            success=False,
            warnings=[
                "HASH_BASED toy misuse fixture could not be verified: "
                f"{exc}"
            ],
        )

    if (
        result.verified
        and result.target_name == plan.target.name
        and result.digest_bits == plan.target.n
        and result.hash_function == plan.target.hash_function
        and result.public
        and not result.security_claim
        and result.record_count == operator.params.get("record_count")
        and result.issue_count == operator.params.get("expected_reuse_groups")
        and result.salt_bytes == operator.params.get("salt_bytes")
    ):
        return ReproductionResult(
            attempted=True,
            status="instance_solved",
            success=True,
            score=HASH_BASED_INSTANCE_REPRODUCTION_SCORE,
            warnings=[
                "Verified a public toy SHAKE256 reused-salt misuse fixture; "
                "this is reproducibility plumbing, not misuse exploit "
                "evidence and not a security claim."
            ],
        )
    return ReproductionResult(
        attempted=True,
        status="failed",
        success=False,
        warnings=[
            "HASH_BASED toy misuse fixture did not produce the expected "
            "public target verification."
        ],
    )


def _resolve_fixture_path(value: str) -> tuple[Path | None, list[str]]:
    fixture_path = Path(value)
    if _is_scoped_preimage_fixture_path(fixture_path):
        return _resolve_package_fixture_path(fixture_path)
    if _is_scoped_signature_fixture_path(fixture_path):
        return _resolve_package_fixture_path(fixture_path)
    if _is_scoped_misuse_fixture_path(fixture_path):
        return _resolve_package_fixture_path(fixture_path)
    return (
        None,
        [
            "HASH_BASED reproduction fixtures must be relative paths under "
            "benchmarks/hash_based_toy_bound/fixtures/ or "
            "benchmarks/hash_based_toy_signature/fixtures/ or "
            "benchmarks/hash_based_toy_misuse/fixtures/."
        ],
    )


def _resolve_package_fixture_path(fixture_path: Path) -> tuple[Path | None, list[str]]:
    root_parts = _fixture_root_parts_for_path(fixture_path)
    return resolve_public_fixture_path(
        str(fixture_path),
        repo_root=ROOT,
        package_fixture_dir=PACKAGE_FIXTURES,
        root_parts=root_parts,
        family_label="HASH_BASED",
    )


def _fixture_root_parts_for_path(fixture_path: Path) -> tuple[str, str, str]:
    if _is_scoped_misuse_fixture_path(fixture_path):
        return _MISUSE_FIXTURE_ROOT_PARTS
    if _is_scoped_signature_fixture_path(fixture_path):
        return _SIGNATURE_FIXTURE_ROOT_PARTS
    return _PREIMAGE_FIXTURE_ROOT_PARTS


def _is_scoped_preimage_fixture_path(path: Path) -> bool:
    return _is_scoped_fixture_path(path, _PREIMAGE_FIXTURE_ROOT_PARTS)


def _is_scoped_signature_fixture_path(path: Path) -> bool:
    return _is_scoped_fixture_path(path, _SIGNATURE_FIXTURE_ROOT_PARTS)


def _is_scoped_misuse_fixture_path(path: Path) -> bool:
    return _is_scoped_fixture_path(path, _MISUSE_FIXTURE_ROOT_PARTS)


def _is_scoped_fixture_path(path: Path, root_parts: tuple[str, ...]) -> bool:
    return is_scoped_public_fixture_path(path, root_parts)
