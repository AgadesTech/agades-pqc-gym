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
from agades_pqc_gym.families.implementation_security.benchmark_fixture import (
    ToyBenchmarkFixtureResult,
    verify_toy_benchmark_fixture,
)
from agades_pqc_gym.families.implementation_security.kat_estimator import (
    TOY_ACVP_ASSUMPTION,
    TOY_ACVP_MAX_TESTS,
    TOY_ACVP_MODEL,
    TOY_BENCHMARK_ASSUMPTION,
    TOY_BENCHMARK_METRIC,
    TOY_BENCHMARK_MODEL,
    TOY_BINARY_SIZE_ASSUMPTION,
    TOY_BINARY_SIZE_METRIC,
    TOY_BINARY_SIZE_MODEL,
    TOY_CTGRIND_TAINT_ASSUMPTION,
    TOY_CTGRIND_TAINT_MODEL,
    TOY_CTGRIND_TAINT_TOOL,
    TOY_DUDECT_SUMMARY_ASSUMPTION,
    TOY_DUDECT_SUMMARY_MODEL,
    TOY_DUDECT_SUMMARY_TOOL,
    TOY_KAT_ASSUMPTION,
    TOY_KAT_MAX_PAYLOAD_BYTES,
    TOY_KAT_MAX_VECTOR_COUNT,
    TOY_KAT_MODEL,
    TOY_MEMORY_ASSUMPTION,
    TOY_MEMORY_METRIC,
    TOY_MEMORY_MODEL,
    TOY_STACK_USAGE_ASSUMPTION,
    TOY_STACK_USAGE_METRIC,
    TOY_STACK_USAGE_MODEL,
    TOY_TIMING_ASSUMPTION,
    TOY_TIMING_MODEL,
    TOY_TIMING_TOOL,
    ToyImplementationSecurityEstimator,
    analyze_toy_acvp_vector_set,
    median,
    payload_sha256,
    required_benchmark_samples,
    required_benchmark_threshold,
    required_binary_size_bytes,
    required_binary_size_threshold,
    required_ctgrind_checked_blocks,
    required_ctgrind_taint_count,
    required_cycle_list,
    required_memory_bytes,
    required_memory_threshold,
    required_positive_number,
    required_stack_samples,
    welch_abs_t,
)
from agades_pqc_gym.families.implementation_security.kat_fixture import (
    verify_toy_acvp_fixture,
    verify_toy_kat_fixture,
)
from agades_pqc_gym.families.implementation_security.timing_fixture import (
    ToyCtgrindTaintFixtureResult,
    ToyTimingFixtureResult,
    verify_toy_ctgrind_taint_fixture,
    verify_toy_timing_fixture,
)
from agades_pqc_gym.families.schema_only import (
    SCHEMA_ONLY_ASSUMPTION,
    SchemaOnlyFamilyAdapter,
)

_SCHEMA_PLACEHOLDER_PARAM_BY_OPERATOR = {
    "benchmark_harness": "metric",
    "constant_time_check": "tool",
    "kat_conformance": "suite",
}
_LIVE_ARTIFACT_PARAM_KEYS = frozenset(
    {
        "binary_path",
        "device_id",
        "host",
        "ip",
        "ssh_target",
        "target_url",
        "trace_path",
    }
)
IMPLEMENTATION_SECURITY_INSTANCE_REPRODUCTION_SCORE = 0.4
ROOT = Path(__file__).resolve().parents[4]
PACKAGE_FIXTURES = Path(__file__).resolve().parent / "fixtures"
_KAT_FIXTURE_ROOT_PARTS = (
    "benchmarks",
    "implementation_security_toy_kat",
    "fixtures",
)
_TIMING_FIXTURE_ROOT_PARTS = (
    "benchmarks",
    "implementation_security_toy_timing",
    "fixtures",
)
_BENCHMARK_FIXTURE_ROOT_PARTS = (
    "benchmarks",
    "implementation_security_toy_benchmark",
    "fixtures",
)


@dataclass(frozen=True)
class ImplementationSecurityFamilyAdapter:
    family: TargetFamily = TargetFamily.IMPLEMENTATION_SECURITY
    support_level: str = "toy_evaluator"
    estimator_name: str = ToyImplementationSecurityEstimator.estimator_name

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "_schema_only",
            SchemaOnlyFamilyAdapter(
                family=TargetFamily.IMPLEMENTATION_SECURITY,
                estimator_name="implementation-security-placeholder-evaluator",
            ),
        )
        object.__setattr__(self, "_estimator", ToyImplementationSecurityEstimator())

    def validate_target(self, target: TargetSpec) -> list[ValidationFinding]:
        findings = _validate_implementation_security_shape(target)
        if target.family is not TargetFamily.IMPLEMENTATION_SECURITY:
            return findings
        if target.support_level is SupportLevel.SCHEMA_ONLY:
            return [*findings, *self._schema_only.validate_target(target)]
        if target.support_level is not SupportLevel.IMPLEMENTED:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="implementation_security_support_level_unknown",
                    message=(
                        "IMPLEMENTATION_SECURITY targets must be schema_only or "
                        "implemented for the reviewed toy implementation-security "
                        "evaluator"
                    ),
                )
            )
            return findings

        if not target.name.startswith("toy_"):
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="implementation_security_toy_target_required",
                    message=(
                        "IMPLEMENTATION_SECURITY implemented evaluator is "
                        "limited to toy_ implementation-security targets"
                    ),
                )
            )
        if target.claimed_security_bits is not None:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="implementation_security_claimed_security_not_allowed",
                    message=(
                        "IMPLEMENTATION_SECURITY toy targets must not include "
                        "claimed_security_bits"
                    ),
                )
            )
        return findings

    def validate_plan(self, plan: AttackPlan) -> list[ValidationFinding]:
        if plan.target.support_level is SupportLevel.SCHEMA_ONLY:
            return self._validate_schema_only_plan(plan)

        findings: list[ValidationFinding] = []
        for operator in plan.operators:
            live_keys = sorted(set(operator.params) & _LIVE_ARTIFACT_PARAM_KEYS)
            for key in live_keys:
                findings.append(
                    ValidationFinding(
                        severity="error",
                        code="implementation_security_live_artifact_not_allowed",
                        message=(
                            "IMPLEMENTATION_SECURITY plans must not reference "
                            f"executable/live artifact parameter {key}"
                        ),
                    )
                )

            if SCHEMA_ONLY_ASSUMPTION in operator.assumptions:
                findings.append(
                    ValidationFinding(
                        severity="error",
                        code=(
                            "implementation_security_schema_only_assumption_on_"
                            "implemented_plan"
                        ),
                        message=(
                            "IMPLEMENTATION_SECURITY implemented toy plans must "
                            f"not use {SCHEMA_ONLY_ASSUMPTION}"
                        ),
                    )
                )
            if operator.type == "kat_conformance":
                findings.extend(_validate_kat_operator(operator))
            elif operator.type == "constant_time_check":
                findings.extend(_validate_timing_operator(operator))
            elif operator.type == "benchmark_harness":
                findings.extend(_validate_benchmark_operator(operator))
            else:
                findings.append(
                    ValidationFinding(
                        severity="error",
                        code="implementation_security_unreviewed_operator",
                        message=(
                            "IMPLEMENTATION_SECURITY implemented evaluator "
                            "supports only kat_conformance, "
                            "constant_time_check, or benchmark_harness toy "
                            "surfaces"
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
                    code="implementation_security_reproduction_fixture_required",
                    message=(
                        "IMPLEMENTATION_SECURITY toy reproduction requires an "
                        "explicit public fixture"
                    ),
                )
            )
        if plan.constraints.downscaled_reproduction_fixture is not None:
            fixture_path = Path(plan.constraints.downscaled_reproduction_fixture)
            root_parts = _fixture_root_parts_for_plan(plan)
            if not _is_scoped_fixture_path(fixture_path, root_parts):
                findings.append(
                    ValidationFinding(
                        severity="error",
                        code="implementation_security_reproduction_fixture_scope",
                        message=(
                            "IMPLEMENTATION_SECURITY reproduction fixtures must "
                            f"be relative paths under {_fixture_scope(root_parts)}"
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
                    code="implementation_security_pre_evaluation_claims_not_allowed",
                    message=(
                        "IMPLEMENTATION_SECURITY toy plans must not include "
                        "estimate claims"
                    ),
                )
            )
        return findings

    def supported_operators(self) -> set[str]:
        return set(PLACEHOLDER_OPERATORS[TargetFamily.IMPLEMENTATION_SECURITY])

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
                    "IMPLEMENTATION_SECURITY toy reproduction requires an "
                    "explicit public fixture."
                ],
            )

        fixture_path, fixture_warnings = _resolve_fixture_path(
            fixture_path_value,
            _fixture_root_parts_for_plan(plan),
        )
        if fixture_path is None:
            return ReproductionResult(
                attempted=False,
                status="not_applicable",
                success=False,
                warnings=fixture_warnings,
            )
        if _is_timing_plan(plan):
            return _reproduce_timing(plan, fixture_path)
        if _is_benchmark_plan(plan):
            return _reproduce_benchmark(plan, fixture_path)

        operator = _kat_operator(plan)
        if operator.params.get("model") == TOY_ACVP_MODEL:
            return _reproduce_acvp(plan, operator, fixture_path)
        return _reproduce_kat(plan, operator, fixture_path)

    def _validate_schema_only_plan(
        self,
        plan: AttackPlan,
    ) -> list[ValidationFinding]:
        findings = self._schema_only.validate_plan(plan)
        for operator in plan.operators:
            live_keys = sorted(set(operator.params) & _LIVE_ARTIFACT_PARAM_KEYS)
            for key in live_keys:
                findings.append(
                    ValidationFinding(
                        severity="error",
                        code="implementation_security_live_artifact_not_allowed",
                        message=(
                            "IMPLEMENTATION_SECURITY schema-only plans must not "
                            "reference executable/live artifact parameter "
                            f"{key}"
                        ),
                    )
                )

            placeholder_param = _SCHEMA_PLACEHOLDER_PARAM_BY_OPERATOR.get(
                operator.type
            )
            if placeholder_param is None:
                findings.append(
                    ValidationFinding(
                        severity="error",
                        code="implementation_security_placeholder_contract_missing",
                        message=(
                            "IMPLEMENTATION_SECURITY schema-only operator "
                            f"{operator.type} has no reviewed placeholder "
                            "parameter contract"
                        ),
                    )
                )
                continue

            value = operator.params.get(placeholder_param)
            if isinstance(value, str) and value.endswith("_schema_placeholder"):
                continue
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="implementation_security_placeholder_required",
                    message=(
                        "IMPLEMENTATION_SECURITY schema-only operator "
                        f"{operator.type} requires placeholder parameter "
                        f"{placeholder_param} ending in _schema_placeholder"
                    ),
                )
            )
        return findings


def _reproduce_kat(
    plan: AttackPlan,
    operator: AttackOperator,
    fixture_path: Path,
) -> ReproductionResult:
    try:
        result = verify_toy_kat_fixture(fixture_path)
    except (OSError, ValueError) as exc:
        return ReproductionResult(
            attempted=True,
            status="failed",
            success=False,
            warnings=[
                "IMPLEMENTATION_SECURITY toy KAT fixture could not be "
                f"verified: {exc}"
            ],
        )

    if (
        result.verified
        and result.target_name == plan.target.name
        and result.suite == operator.params.get("suite")
        and result.model == operator.params.get("model")
        and result.expected_sha256 == operator.params.get("expected_sha256")
        and result.vector_count == operator.params.get("vector_count")
        and not result.artifact_execution
        and result.public
        and not result.security_claim
    ):
        return ReproductionResult(
            attempted=True,
            status="instance_solved",
            success=True,
            score=IMPLEMENTATION_SECURITY_INSTANCE_REPRODUCTION_SCORE,
            warnings=[
                "Verified a public JSON-only toy KAT digest fixture without "
                "executing artifacts; this is reproducibility plumbing, not "
                "a conformance, side-channel, or security claim."
            ],
        )
    return ReproductionResult(
        attempted=True,
        status="failed",
        success=False,
        warnings=[
            "IMPLEMENTATION_SECURITY toy KAT fixture did not match the "
            "expected public no-execution plan."
        ],
    )


def _reproduce_acvp(
    plan: AttackPlan,
    operator: AttackOperator,
    fixture_path: Path,
) -> ReproductionResult:
    try:
        result = verify_toy_acvp_fixture(fixture_path)
    except (OSError, ValueError) as exc:
        return ReproductionResult(
            attempted=True,
            status="failed",
            success=False,
            warnings=[
                "IMPLEMENTATION_SECURITY toy ACVP fixture could not be "
                f"verified: {exc}"
            ],
        )

    expected_digest = operator.params.get("expected_vector_set_sha256")
    if (
        result.verified
        and result.target_name == plan.target.name
        and result.suite == operator.params.get("suite")
        and result.model == operator.params.get("model")
        and result.algorithm == operator.params.get("algorithm")
        and result.mode == operator.params.get("mode")
        and result.expected_vector_set_sha256 == expected_digest
        and result.vector_set_sha256 == expected_digest
        and result.test_count == operator.params.get("test_count")
        and not result.artifact_execution
        and result.public
        and not result.security_claim
    ):
        return ReproductionResult(
            attempted=True,
            status="instance_solved",
            success=True,
            score=IMPLEMENTATION_SECURITY_INSTANCE_REPRODUCTION_SCORE,
            warnings=[
                "Verified a public JSON-only toy ACVP vector-set fixture without "
                "executing artifacts; this is reproducibility plumbing, not an "
                "ACVP certificate, conformance, side-channel, or security claim."
            ],
        )
    return ReproductionResult(
        attempted=True,
        status="failed",
        success=False,
        warnings=[
            "IMPLEMENTATION_SECURITY toy ACVP fixture did not match the "
            "expected public no-execution plan."
        ],
    )


def _validate_implementation_security_shape(
    target: TargetSpec,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    if target.family is not TargetFamily.IMPLEMENTATION_SECURITY:
        findings.append(
            ValidationFinding(
                severity="error",
                code="family_adapter_mismatch",
                message=(
                    "IMPLEMENTATION_SECURITY adapter cannot validate "
                    f"{target.family.value} targets"
                ),
            )
        )
        return findings

    if (
        target.support_level is SupportLevel.SCHEMA_ONLY
        and not target.name.lower().endswith("_schema")
    ):
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_schema_fixture_required",
                message=(
                    "IMPLEMENTATION_SECURITY target name must identify a "
                    "schema-only fixture"
                ),
            )
        )
    return findings


def _validate_kat_operator(operator: AttackOperator) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    model = operator.params.get("model")
    if model == TOY_KAT_MODEL:
        if TOY_KAT_ASSUMPTION not in operator.assumptions:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="implementation_security_toy_kat_assumption_required",
                    message=(
                        "IMPLEMENTATION_SECURITY toy KAT plans must include "
                        f"{TOY_KAT_ASSUMPTION}"
                    ),
                )
            )
        findings.extend(_validate_toy_kat_params(operator.params))
        return findings

    if model == TOY_ACVP_MODEL:
        if TOY_ACVP_ASSUMPTION not in operator.assumptions:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="implementation_security_toy_acvp_assumption_required",
                    message=(
                        "IMPLEMENTATION_SECURITY toy ACVP plans must include "
                        f"{TOY_ACVP_ASSUMPTION}"
                    ),
                )
            )
        findings.extend(_validate_toy_acvp_params(operator.params))
        return findings

    if model not in {TOY_KAT_MODEL, TOY_ACVP_MODEL}:
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_unreviewed_kat_model",
                message=(
                    "IMPLEMENTATION_SECURITY implemented evaluator supports only "
                    "kat_conformance with model="
                    f"{TOY_KAT_MODEL} or model={TOY_ACVP_MODEL}"
                ),
            )
        )
    return findings


def _validate_timing_operator(operator: AttackOperator) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    tool = operator.params.get("tool")
    model = operator.params.get("model")
    reviewed_pair: tuple[str, str] | None = None
    if tool == TOY_TIMING_TOOL and model == TOY_TIMING_MODEL:
        reviewed_pair = (TOY_TIMING_TOOL, TOY_TIMING_MODEL)
        required_assumption = TOY_TIMING_ASSUMPTION
        assumption_error_code = "implementation_security_toy_timing_assumption_required"
        assumption_surface = "toy timing"
    elif tool == TOY_DUDECT_SUMMARY_TOOL and model == TOY_DUDECT_SUMMARY_MODEL:
        reviewed_pair = (TOY_DUDECT_SUMMARY_TOOL, TOY_DUDECT_SUMMARY_MODEL)
        required_assumption = TOY_DUDECT_SUMMARY_ASSUMPTION
        assumption_error_code = (
            "implementation_security_toy_dudect_summary_assumption_required"
        )
        assumption_surface = "toy dudect summary"
    elif tool == TOY_CTGRIND_TAINT_TOOL and model == TOY_CTGRIND_TAINT_MODEL:
        reviewed_pair = (TOY_CTGRIND_TAINT_TOOL, TOY_CTGRIND_TAINT_MODEL)
        required_assumption = TOY_CTGRIND_TAINT_ASSUMPTION
        assumption_error_code = (
            "implementation_security_toy_ctgrind_taint_assumption_required"
        )
        assumption_surface = "toy ctgrind secret-taint summary"
    else:
        required_assumption = None
        assumption_error_code = ""
        assumption_surface = ""

    reviewed_tools = {
        TOY_TIMING_TOOL,
        TOY_DUDECT_SUMMARY_TOOL,
        TOY_CTGRIND_TAINT_TOOL,
    }
    reviewed_models = {
        TOY_TIMING_MODEL,
        TOY_DUDECT_SUMMARY_MODEL,
        TOY_CTGRIND_TAINT_MODEL,
    }
    if tool not in reviewed_tools:
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_unreviewed_timing_tool",
                message=(
                    "IMPLEMENTATION_SECURITY constant_time_check supports only "
                    f"reviewed tools: {TOY_TIMING_TOOL}, "
                    f"{TOY_DUDECT_SUMMARY_TOOL}, {TOY_CTGRIND_TAINT_TOOL}"
                ),
            )
        )
    if model not in reviewed_models:
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_unreviewed_timing_model",
                message=(
                    "IMPLEMENTATION_SECURITY constant_time_check supports only "
                    f"reviewed models: {TOY_TIMING_MODEL}, "
                    f"{TOY_DUDECT_SUMMARY_MODEL}, {TOY_CTGRIND_TAINT_MODEL}"
                ),
            )
        )
    if reviewed_pair is None and tool in reviewed_tools and model in reviewed_models:
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_timing_pair_mismatch",
                message=(
                    "IMPLEMENTATION_SECURITY constant_time_check requires a "
                    "reviewed tool/model pair"
                ),
            )
        )
    if (
        required_assumption is not None
        and required_assumption not in operator.assumptions
    ):
        findings.append(
            ValidationFinding(
                severity="error",
                code=assumption_error_code,
                message=(
                    f"IMPLEMENTATION_SECURITY {assumption_surface} plans must "
                    f"include {required_assumption}"
                ),
            )
        )
    if reviewed_pair in {
        (TOY_TIMING_TOOL, TOY_TIMING_MODEL),
        (TOY_DUDECT_SUMMARY_TOOL, TOY_DUDECT_SUMMARY_MODEL),
    }:
        findings.extend(_validate_toy_timing_params(operator.params))
    if reviewed_pair == (TOY_DUDECT_SUMMARY_TOOL, TOY_DUDECT_SUMMARY_MODEL):
        findings.extend(_validate_toy_dudect_summary_params(operator.params))
    if reviewed_pair == (TOY_CTGRIND_TAINT_TOOL, TOY_CTGRIND_TAINT_MODEL):
        findings.extend(_validate_toy_ctgrind_taint_params(operator.params))
    return findings


def _validate_benchmark_operator(
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    metric = operator.params.get("metric")
    model = operator.params.get("model")

    if model == TOY_BINARY_SIZE_MODEL:
        if metric != TOY_BINARY_SIZE_METRIC:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="implementation_security_unreviewed_binary_size_metric",
                    message=(
                        "IMPLEMENTATION_SECURITY binary-size benchmark "
                        f"supports only metric={TOY_BINARY_SIZE_METRIC}"
                    ),
                )
            )
        if TOY_BINARY_SIZE_ASSUMPTION not in operator.assumptions:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code=(
                        "implementation_security_toy_binary_size_assumption_"
                        "required"
                    ),
                    message=(
                        "IMPLEMENTATION_SECURITY toy binary-size plans must "
                        f"include {TOY_BINARY_SIZE_ASSUMPTION}"
                    ),
                )
            )
        findings.extend(_validate_toy_binary_size_params(operator.params))
        return findings

    if model == TOY_MEMORY_MODEL:
        if metric != TOY_MEMORY_METRIC:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="implementation_security_unreviewed_memory_metric",
                    message=(
                        "IMPLEMENTATION_SECURITY memory benchmark supports "
                        f"only metric={TOY_MEMORY_METRIC}"
                    ),
                )
            )
        if TOY_MEMORY_ASSUMPTION not in operator.assumptions:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="implementation_security_toy_memory_assumption_required",
                    message=(
                        "IMPLEMENTATION_SECURITY toy memory plans must include "
                        f"{TOY_MEMORY_ASSUMPTION}"
                    ),
                )
            )
        findings.extend(_validate_toy_memory_params(operator.params))
        return findings

    if model == TOY_STACK_USAGE_MODEL:
        if metric != TOY_STACK_USAGE_METRIC:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="implementation_security_unreviewed_stack_usage_metric",
                    message=(
                        "IMPLEMENTATION_SECURITY stack-usage benchmark supports "
                        f"only metric={TOY_STACK_USAGE_METRIC}"
                    ),
                )
            )
        if TOY_STACK_USAGE_ASSUMPTION not in operator.assumptions:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code=(
                        "implementation_security_toy_stack_usage_assumption_"
                        "required"
                    ),
                    message=(
                        "IMPLEMENTATION_SECURITY toy stack-usage plans must "
                        f"include {TOY_STACK_USAGE_ASSUMPTION}"
                    ),
                )
            )
        findings.extend(_validate_toy_stack_usage_params(operator.params))
        return findings

    if metric != TOY_BENCHMARK_METRIC:
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_unreviewed_benchmark_metric",
                message=(
                    "IMPLEMENTATION_SECURITY benchmark_harness supports only "
                    f"metric={TOY_BENCHMARK_METRIC}"
                ),
            )
        )
    if model != TOY_BENCHMARK_MODEL:
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_unreviewed_benchmark_model",
                message=(
                    "IMPLEMENTATION_SECURITY benchmark_harness supports only "
                    f"model={TOY_BENCHMARK_MODEL}"
                ),
            )
        )
    if TOY_BENCHMARK_ASSUMPTION not in operator.assumptions:
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_toy_benchmark_assumption_required",
                message=(
                    "IMPLEMENTATION_SECURITY toy benchmark plans must include "
                    f"{TOY_BENCHMARK_ASSUMPTION}"
                ),
            )
        )
    findings.extend(_validate_toy_benchmark_params(operator.params))
    return findings


def _validate_toy_kat_params(params: dict[str, object]) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    payload = params.get("payload")
    expected_sha256 = params.get("expected_sha256")
    vector_count = params.get("vector_count")

    if not isinstance(payload, str):
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_kat_payload_required",
                message="IMPLEMENTATION_SECURITY toy KAT requires string payload",
            )
        )
    elif not payload:
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_kat_payload_empty",
                message="IMPLEMENTATION_SECURITY toy KAT payload must be non-empty",
            )
        )
    elif len(payload.encode("utf-8")) > TOY_KAT_MAX_PAYLOAD_BYTES:
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_kat_payload_too_large",
                message=(
                    "IMPLEMENTATION_SECURITY toy KAT payload must be at most "
                    f"{TOY_KAT_MAX_PAYLOAD_BYTES} bytes"
                ),
            )
        )

    if not (isinstance(expected_sha256, str) and _is_sha256_hex(expected_sha256)):
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_kat_digest_required",
                message=(
                    "IMPLEMENTATION_SECURITY toy KAT requires expected_sha256 "
                    "as 64 lowercase hex characters"
                ),
            )
        )
    elif isinstance(payload, str) and expected_sha256 != payload_sha256(payload):
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_kat_digest_mismatch",
                message=(
                    "IMPLEMENTATION_SECURITY toy KAT expected_sha256 must match "
                    "SHA-256(payload)"
                ),
            )
        )

    if not isinstance(vector_count, int) or isinstance(vector_count, bool):
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_kat_vector_count_required",
                message="IMPLEMENTATION_SECURITY toy KAT requires vector_count",
            )
        )
    elif not 1 <= vector_count <= TOY_KAT_MAX_VECTOR_COUNT:
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_kat_vector_count_limit",
                message=(
                    "IMPLEMENTATION_SECURITY toy KAT requires "
                    f"1 <= vector_count <= {TOY_KAT_MAX_VECTOR_COUNT}"
                ),
            )
        )
    return findings


def _validate_toy_acvp_params(params: dict[str, object]) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    suite = params.get("suite")
    algorithm = params.get("algorithm")
    mode = params.get("mode")
    vector_set = params.get("vector_set")
    expected_digest = params.get("expected_vector_set_sha256")
    test_count = params.get("test_count")

    if not isinstance(suite, str) or not suite:
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_acvp_suite_required",
                message=(
                    "IMPLEMENTATION_SECURITY toy ACVP requires non-empty suite"
                ),
            )
        )
    if not isinstance(algorithm, str) or not algorithm:
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_acvp_algorithm_required",
                message=(
                    "IMPLEMENTATION_SECURITY toy ACVP requires non-empty "
                    "algorithm"
                ),
            )
        )
    if not isinstance(mode, str) or not mode:
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_acvp_mode_required",
                message="IMPLEMENTATION_SECURITY toy ACVP requires non-empty mode",
            )
        )
    if not isinstance(vector_set, dict):
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_acvp_vector_set_required",
                message=(
                    "IMPLEMENTATION_SECURITY toy ACVP requires vector_set object"
                ),
            )
        )
    if not (isinstance(expected_digest, str) and _is_sha256_hex(expected_digest)):
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_acvp_digest_required",
                message=(
                    "IMPLEMENTATION_SECURITY toy ACVP requires "
                    "expected_vector_set_sha256 as 64 lowercase hex characters"
                ),
            )
        )
    if not isinstance(test_count, int) or isinstance(test_count, bool):
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_acvp_test_count_required",
                message="IMPLEMENTATION_SECURITY toy ACVP requires test_count",
            )
        )
    elif not 1 <= test_count <= TOY_ACVP_MAX_TESTS:
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_acvp_test_count_limit",
                message=(
                    "IMPLEMENTATION_SECURITY toy ACVP requires "
                    f"1 <= test_count <= {TOY_ACVP_MAX_TESTS}"
                ),
            )
        )

    if findings:
        return findings

    assert isinstance(vector_set, dict)
    assert isinstance(algorithm, str)
    assert isinstance(mode, str)
    assert isinstance(expected_digest, str)
    assert isinstance(test_count, int)
    try:
        summary = analyze_toy_acvp_vector_set(vector_set, algorithm, mode)
    except ValueError as exc:
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_acvp_vector_set_invalid",
                message=f"IMPLEMENTATION_SECURITY toy ACVP {exc}",
            )
        )
        return findings

    if summary.vector_set_sha256 != expected_digest:
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_acvp_digest_mismatch",
                message=(
                    "IMPLEMENTATION_SECURITY toy ACVP "
                    "expected_vector_set_sha256 must match canonical "
                    "SHA-256(vector_set)"
                ),
            )
        )
    if summary.test_count != test_count:
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_acvp_test_count_mismatch",
                message=(
                    "IMPLEMENTATION_SECURITY toy ACVP test_count must match "
                    "vector_set tests"
                ),
            )
        )
    return findings


def _validate_toy_benchmark_params(
    params: dict[str, object],
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    suite = params.get("suite")
    samples = _benchmark_samples_or_error(params, "samples", findings)
    max_median_cycles = _benchmark_threshold_or_error(
        params,
        "max_median_cycles",
        findings,
    )
    if not isinstance(suite, str) or not suite:
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_benchmark_suite_required",
                message=(
                    "IMPLEMENTATION_SECURITY toy benchmark requires non-empty "
                    "suite"
                ),
            )
        )
    if (
        samples is not None
        and max_median_cycles is not None
        and median(samples) > max_median_cycles
    ):
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_benchmark_threshold_failed",
                message=(
                    "IMPLEMENTATION_SECURITY toy benchmark median cycles exceeds "
                    "max_median_cycles"
                ),
            )
        )
    return findings


def _validate_toy_binary_size_params(
    params: dict[str, object],
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    suite = params.get("suite")
    text_bytes = _binary_size_bytes_or_error(params, "text_bytes", findings)
    rodata_bytes = _binary_size_bytes_or_error(params, "rodata_bytes", findings)
    data_bytes = _binary_size_bytes_or_error(params, "data_bytes", findings)
    bss_bytes = _binary_size_bytes_or_error(params, "bss_bytes", findings)
    max_total_bytes = _binary_size_threshold_or_error(
        params,
        "max_total_bytes",
        findings,
    )
    if not isinstance(suite, str) or not suite:
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_binary_size_suite_required",
                message=(
                    "IMPLEMENTATION_SECURITY toy binary size requires "
                    "non-empty suite"
                ),
            )
        )
    if (
        text_bytes is not None
        and rodata_bytes is not None
        and data_bytes is not None
        and bss_bytes is not None
        and text_bytes + rodata_bytes + data_bytes + bss_bytes <= 0
    ):
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_binary_size_total_required",
                message=(
                    "IMPLEMENTATION_SECURITY toy binary size requires positive "
                    "total bytes"
                ),
            )
        )
    if (
        text_bytes is not None
        and rodata_bytes is not None
        and data_bytes is not None
        and bss_bytes is not None
        and max_total_bytes is not None
        and text_bytes + rodata_bytes + data_bytes + bss_bytes > max_total_bytes
    ):
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_binary_size_total_threshold",
                message=(
                    "IMPLEMENTATION_SECURITY toy binary size total binary "
                    "size exceeds max_total_bytes"
                ),
            )
        )
    return findings


def _validate_toy_memory_params(params: dict[str, object]) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    suite = params.get("suite")
    stack_bytes = _memory_bytes_or_error(params, "stack_bytes", findings)
    heap_bytes = _memory_bytes_or_error(params, "heap_bytes", findings)
    code_bytes = _memory_bytes_or_error(params, "code_bytes", findings)
    max_stack_bytes = _memory_threshold_or_error(
        params,
        "max_stack_bytes",
        findings,
    )
    max_heap_bytes = _memory_threshold_or_error(
        params,
        "max_heap_bytes",
        findings,
    )
    max_code_bytes = _memory_threshold_or_error(
        params,
        "max_code_bytes",
        findings,
    )
    if not isinstance(suite, str) or not suite:
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_memory_suite_required",
                message=(
                    "IMPLEMENTATION_SECURITY toy memory requires non-empty suite"
                ),
            )
        )
    if (
        stack_bytes is not None
        and heap_bytes is not None
        and code_bytes is not None
        and stack_bytes + heap_bytes + code_bytes <= 0
    ):
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_memory_total_required",
                message=(
                    "IMPLEMENTATION_SECURITY toy memory requires positive "
                    "total bytes"
                ),
            )
        )
    for observed_name, observed, threshold_name, threshold in (
        ("stack_bytes", stack_bytes, "max_stack_bytes", max_stack_bytes),
        ("heap_bytes", heap_bytes, "max_heap_bytes", max_heap_bytes),
        ("code_bytes", code_bytes, "max_code_bytes", max_code_bytes),
    ):
        if observed is None or threshold is None or observed <= threshold:
            continue
        findings.append(
            ValidationFinding(
                severity="error",
                code=f"implementation_security_memory_{observed_name}_threshold",
                message=(
                    "IMPLEMENTATION_SECURITY toy memory "
                    f"{observed_name} exceeds {threshold_name}"
                ),
            )
        )
    return findings


def _validate_toy_stack_usage_params(
    params: dict[str, object],
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    suite = params.get("suite")
    stack_samples = _stack_samples_or_error(params, "stack_samples", findings)
    max_stack_bytes = _memory_threshold_or_error(
        params,
        "max_stack_bytes",
        findings,
    )
    if not isinstance(suite, str) or not suite:
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_stack_usage_suite_required",
                message=(
                    "IMPLEMENTATION_SECURITY toy stack usage requires "
                    "non-empty suite"
                ),
            )
        )
    if (
        stack_samples is not None
        and max_stack_bytes is not None
        and max(stack_samples) > max_stack_bytes
    ):
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_stack_usage_threshold",
                message=(
                    "IMPLEMENTATION_SECURITY toy stack usage observed stack "
                    "usage exceeds max_stack_bytes"
                ),
            )
        )
    return findings


def _validate_toy_timing_params(
    params: dict[str, object],
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    fixed_cycles = _cycle_list_or_error(params, "fixed_cycles", findings)
    random_cycles = _cycle_list_or_error(params, "random_cycles", findings)
    max_abs_t = _positive_number_or_error(params, "max_abs_t", findings)
    if (
        fixed_cycles is not None
        and random_cycles is not None
        and max_abs_t is not None
        and welch_abs_t(fixed_cycles, random_cycles) > max_abs_t
    ):
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_timing_threshold_failed",
                message=(
                    "IMPLEMENTATION_SECURITY toy timing observed abs t-statistic "
                    "exceeds max_abs_t"
                ),
            )
        )
    return findings


def _validate_toy_dudect_summary_params(
    params: dict[str, object],
) -> list[ValidationFinding]:
    dudect_version = params.get("dudect_version")
    if isinstance(dudect_version, str) and dudect_version:
        return []
    return [
        ValidationFinding(
            severity="error",
            code="implementation_security_dudect_version_required",
            message=(
                "IMPLEMENTATION_SECURITY toy dudect summary requires non-empty "
                "dudect_version"
            ),
        )
    ]


def _validate_toy_ctgrind_taint_params(
    params: dict[str, object],
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    ctgrind_version = params.get("ctgrind_version")
    _ctgrind_checked_blocks_or_error(params, findings)
    secret_branch_count = _ctgrind_taint_count_or_error(
        params,
        "secret_dependent_branch_count",
        findings,
    )
    secret_memory_count = _ctgrind_taint_count_or_error(
        params,
        "secret_dependent_memory_access_count",
        findings,
    )
    max_secret_branch_count = _ctgrind_taint_count_or_error(
        params,
        "max_secret_dependent_branch_count",
        findings,
    )
    max_secret_memory_count = _ctgrind_taint_count_or_error(
        params,
        "max_secret_dependent_memory_access_count",
        findings,
    )
    if not isinstance(ctgrind_version, str) or not ctgrind_version:
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_ctgrind_version_required",
                message=(
                    "IMPLEMENTATION_SECURITY toy ctgrind secret-taint summary "
                    "requires non-empty ctgrind_version"
                ),
            )
        )
    if (
        secret_branch_count is not None
        and max_secret_branch_count is not None
        and secret_branch_count > max_secret_branch_count
    ):
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_ctgrind_branch_threshold_failed",
                message=(
                    "IMPLEMENTATION_SECURITY toy ctgrind secret-taint summary "
                    "secret_dependent_branch_count exceeds "
                    "max_secret_dependent_branch_count"
                ),
            )
        )
    if (
        secret_memory_count is not None
        and max_secret_memory_count is not None
        and secret_memory_count > max_secret_memory_count
    ):
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_ctgrind_memory_threshold_failed",
                message=(
                    "IMPLEMENTATION_SECURITY toy ctgrind secret-taint summary "
                    "secret_dependent_memory_access_count exceeds "
                    "max_secret_dependent_memory_access_count"
                ),
            )
        )
    return findings


def _cycle_list_or_error(
    params: dict[str, object],
    name: str,
    findings: list[ValidationFinding],
) -> list[int] | None:
    try:
        return required_cycle_list(params, name)
    except ValueError as exc:
        findings.append(
            ValidationFinding(
                severity="error",
                code=f"implementation_security_timing_{name}_invalid",
                message=str(exc),
            )
        )
        return None


def _ctgrind_checked_blocks_or_error(
    params: dict[str, object],
    findings: list[ValidationFinding],
) -> int | None:
    try:
        return required_ctgrind_checked_blocks(params)
    except ValueError as exc:
        findings.append(
            ValidationFinding(
                severity="error",
                code="implementation_security_ctgrind_checked_blocks_invalid",
                message=str(exc),
            )
        )
        return None


def _ctgrind_taint_count_or_error(
    params: dict[str, object],
    name: str,
    findings: list[ValidationFinding],
) -> int | None:
    try:
        return required_ctgrind_taint_count(params, name)
    except ValueError as exc:
        findings.append(
            ValidationFinding(
                severity="error",
                code=f"implementation_security_ctgrind_{name}_invalid",
                message=str(exc),
            )
        )
        return None


def _positive_number_or_error(
    params: dict[str, object],
    name: str,
    findings: list[ValidationFinding],
) -> float | None:
    try:
        return required_positive_number(params, name)
    except ValueError as exc:
        findings.append(
            ValidationFinding(
                severity="error",
                code=f"implementation_security_timing_{name}_invalid",
                message=str(exc),
            )
        )
        return None


def _benchmark_samples_or_error(
    params: dict[str, object],
    name: str,
    findings: list[ValidationFinding],
) -> list[int] | None:
    try:
        return required_benchmark_samples(params, name)
    except ValueError as exc:
        findings.append(
            ValidationFinding(
                severity="error",
                code=f"implementation_security_benchmark_{name}_invalid",
                message=str(exc),
            )
        )
        return None


def _benchmark_threshold_or_error(
    params: dict[str, object],
    name: str,
    findings: list[ValidationFinding],
) -> float | None:
    try:
        return required_benchmark_threshold(params, name)
    except ValueError as exc:
        findings.append(
            ValidationFinding(
                severity="error",
                code=f"implementation_security_benchmark_{name}_invalid",
                message=str(exc),
            )
        )
        return None


def _memory_bytes_or_error(
    params: dict[str, object],
    name: str,
    findings: list[ValidationFinding],
) -> int | None:
    try:
        return required_memory_bytes(params, name)
    except ValueError as exc:
        findings.append(
            ValidationFinding(
                severity="error",
                code=f"implementation_security_memory_{name}_invalid",
                message=str(exc),
            )
        )
        return None


def _stack_samples_or_error(
    params: dict[str, object],
    name: str,
    findings: list[ValidationFinding],
) -> list[int] | None:
    try:
        return required_stack_samples(params, name)
    except ValueError as exc:
        findings.append(
            ValidationFinding(
                severity="error",
                code=f"implementation_security_stack_usage_{name}_invalid",
                message=str(exc),
            )
        )
        return None


def _binary_size_bytes_or_error(
    params: dict[str, object],
    name: str,
    findings: list[ValidationFinding],
) -> int | None:
    try:
        return required_binary_size_bytes(params, name)
    except ValueError as exc:
        findings.append(
            ValidationFinding(
                severity="error",
                code=f"implementation_security_binary_size_{name}_invalid",
                message=str(exc),
            )
        )
        return None


def _binary_size_threshold_or_error(
    params: dict[str, object],
    name: str,
    findings: list[ValidationFinding],
) -> int | None:
    try:
        return required_binary_size_threshold(params, name)
    except ValueError as exc:
        findings.append(
            ValidationFinding(
                severity="error",
                code=f"implementation_security_binary_size_{name}_invalid",
                message=str(exc),
            )
        )
        return None


def _memory_threshold_or_error(
    params: dict[str, object],
    name: str,
    findings: list[ValidationFinding],
) -> int | None:
    try:
        return required_memory_threshold(params, name)
    except ValueError as exc:
        findings.append(
            ValidationFinding(
                severity="error",
                code=f"implementation_security_memory_{name}_invalid",
                message=str(exc),
            )
        )
        return None


def _is_sha256_hex(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _kat_operator(plan: AttackPlan) -> AttackOperator:
    for operator in plan.operators:
        if operator.type == "kat_conformance":
            return operator
    raise ValueError("IMPLEMENTATION_SECURITY reproduction requires kat_conformance")


def _timing_operator(plan: AttackPlan) -> AttackOperator:
    for operator in plan.operators:
        if operator.type == "constant_time_check":
            return operator
    raise ValueError(
        "IMPLEMENTATION_SECURITY reproduction requires constant_time_check"
    )


def _benchmark_operator(plan: AttackPlan) -> AttackOperator:
    for operator in plan.operators:
        if operator.type == "benchmark_harness":
            return operator
    raise ValueError("IMPLEMENTATION_SECURITY reproduction requires benchmark_harness")


def _reproduce_timing(plan: AttackPlan, fixture_path: Path) -> ReproductionResult:
    operator = _timing_operator(plan)
    if operator.params.get("model") == TOY_CTGRIND_TAINT_MODEL:
        return _reproduce_ctgrind_taint(plan, operator, fixture_path)

    try:
        result = verify_toy_timing_fixture(fixture_path)
    except (OSError, ValueError) as exc:
        return ReproductionResult(
            attempted=True,
            status="failed",
            success=False,
            warnings=[
                "IMPLEMENTATION_SECURITY toy timing fixture could not be "
                f"verified: {exc}"
            ],
        )

    if operator.params.get("model") == TOY_DUDECT_SUMMARY_MODEL:
        return _reproduce_dudect_summary_timing(plan, operator, result)

    if (
        result.verified
        and result.target_name == plan.target.name
        and result.tool == operator.params.get("tool")
        and result.model == operator.params.get("model")
        and result.fixed_cycles == operator.params.get("fixed_cycles")
        and result.random_cycles == operator.params.get("random_cycles")
        and result.max_abs_t == operator.params.get("max_abs_t")
        and not result.artifact_execution
        and result.public
        and not result.security_claim
    ):
        return ReproductionResult(
            attempted=True,
            status="instance_solved",
            success=True,
            score=IMPLEMENTATION_SECURITY_INSTANCE_REPRODUCTION_SCORE,
            warnings=[
                "Verified a public JSON-only toy timing summary fixture without "
                "executing artifacts; this is reproducibility plumbing, not a "
                "constant-time, side-channel, or security claim."
            ],
        )
    return ReproductionResult(
        attempted=True,
        status="failed",
        success=False,
        warnings=[
            "IMPLEMENTATION_SECURITY toy timing fixture did not match the "
            "expected public no-execution plan."
        ],
    )


def _reproduce_dudect_summary_timing(
    plan: AttackPlan,
    operator: AttackOperator,
    result: ToyTimingFixtureResult,
) -> ReproductionResult:
    if (
        result.verified
        and result.target_name == plan.target.name
        and result.tool == operator.params.get("tool")
        and result.model == operator.params.get("model")
        and result.dudect_version == operator.params.get("dudect_version")
        and result.fixed_cycles == operator.params.get("fixed_cycles")
        and result.random_cycles == operator.params.get("random_cycles")
        and result.max_abs_t == operator.params.get("max_abs_t")
        and not result.artifact_execution
        and result.dudect_execution is False
        and result.public
        and result.constant_time_claim is False
        and not result.security_claim
    ):
        return ReproductionResult(
            attempted=True,
            status="instance_solved",
            success=True,
            score=IMPLEMENTATION_SECURITY_INSTANCE_REPRODUCTION_SCORE,
            warnings=[
                "Verified a public JSON-only toy dudect summary fixture without "
                "executing artifacts; this did not execute dudect and is "
                "reproducibility plumbing, not a constant-time, side-channel, "
                "or security claim."
            ],
        )
    return ReproductionResult(
        attempted=True,
        status="failed",
        success=False,
        warnings=[
            "IMPLEMENTATION_SECURITY toy dudect summary fixture did not match "
            "the expected public no-execution plan."
        ],
    )


def _reproduce_ctgrind_taint(
    plan: AttackPlan,
    operator: AttackOperator,
    fixture_path: Path,
) -> ReproductionResult:
    try:
        result = verify_toy_ctgrind_taint_fixture(fixture_path)
    except (OSError, ValueError) as exc:
        return ReproductionResult(
            attempted=True,
            status="failed",
            success=False,
            warnings=[
                "IMPLEMENTATION_SECURITY toy ctgrind secret-taint fixture "
                f"could not be verified: {exc}"
            ],
        )

    return _reproduce_ctgrind_taint_result(plan, operator, result)


def _reproduce_ctgrind_taint_result(
    plan: AttackPlan,
    operator: AttackOperator,
    result: ToyCtgrindTaintFixtureResult,
) -> ReproductionResult:
    expected_fields = (
        "checked_blocks",
        "secret_dependent_branch_count",
        "secret_dependent_memory_access_count",
        "max_secret_dependent_branch_count",
        "max_secret_dependent_memory_access_count",
    )
    if (
        result.verified
        and result.target_name == plan.target.name
        and result.tool == operator.params.get("tool")
        and result.model == operator.params.get("model")
        and result.ctgrind_version == operator.params.get("ctgrind_version")
        and all(
            getattr(result, field) == operator.params.get(field)
            for field in expected_fields
        )
        and not result.artifact_execution
        and result.ctgrind_execution is False
        and result.public
        and result.constant_time_claim is False
        and not result.security_claim
    ):
        return ReproductionResult(
            attempted=True,
            status="instance_solved",
            success=True,
            score=IMPLEMENTATION_SECURITY_INSTANCE_REPRODUCTION_SCORE,
            warnings=[
                "Verified a public JSON-only toy ctgrind secret-taint fixture "
                "without executing artifacts; this did not execute ctgrind "
                "and is reproducibility plumbing, not a constant-time, "
                "side-channel, or security claim."
            ],
        )
    return ReproductionResult(
        attempted=True,
        status="failed",
        success=False,
        warnings=[
            "IMPLEMENTATION_SECURITY toy ctgrind secret-taint fixture did not "
            "match the expected public no-execution plan."
        ],
    )


def _reproduce_benchmark(plan: AttackPlan, fixture_path: Path) -> ReproductionResult:
    try:
        result = verify_toy_benchmark_fixture(fixture_path)
    except (OSError, ValueError) as exc:
        return ReproductionResult(
            attempted=True,
            status="failed",
            success=False,
            warnings=[
                "IMPLEMENTATION_SECURITY toy benchmark fixture could not be "
                f"verified: {exc}"
            ],
        )

    operator = _benchmark_operator(plan)
    if operator.params.get("model") == TOY_BINARY_SIZE_MODEL:
        return _reproduce_binary_size_benchmark(plan, operator, result)
    if operator.params.get("model") == TOY_MEMORY_MODEL:
        return _reproduce_memory_benchmark(plan, operator, result)
    if operator.params.get("model") == TOY_STACK_USAGE_MODEL:
        return _reproduce_stack_usage_benchmark(plan, operator, result)

    if (
        result.verified
        and result.target_name == plan.target.name
        and result.suite == operator.params.get("suite")
        and result.metric == operator.params.get("metric")
        and result.model == operator.params.get("model")
        and result.samples == operator.params.get("samples")
        and result.max_median_cycles == operator.params.get("max_median_cycles")
        and not result.artifact_execution
        and result.public
        and not result.security_claim
    ):
        return ReproductionResult(
            attempted=True,
            status="instance_solved",
            success=True,
            score=IMPLEMENTATION_SECURITY_INSTANCE_REPRODUCTION_SCORE,
            warnings=[
                "Verified a public JSON-only toy benchmark summary fixture "
                "without executing artifacts; this is reproducibility plumbing, "
                "not a performance, conformance, side-channel, or security claim."
            ],
        )
    return ReproductionResult(
        attempted=True,
        status="failed",
        success=False,
        warnings=[
            "IMPLEMENTATION_SECURITY toy benchmark fixture did not match the "
            "expected public no-execution plan."
        ],
    )


def _reproduce_binary_size_benchmark(
    plan: AttackPlan,
    operator: AttackOperator,
    result: ToyBenchmarkFixtureResult,
) -> ReproductionResult:
    expected_fields = (
        "text_bytes",
        "rodata_bytes",
        "data_bytes",
        "bss_bytes",
        "max_total_bytes",
    )
    if (
        getattr(result, "verified", False)
        and getattr(result, "target_name", None) == plan.target.name
        and getattr(result, "suite", None) == operator.params.get("suite")
        and getattr(result, "metric", None) == operator.params.get("metric")
        and getattr(result, "model", None) == operator.params.get("model")
        and all(
            getattr(result, field, None) == operator.params.get(field)
            for field in expected_fields
        )
        and not getattr(result, "artifact_execution", True)
        and getattr(result, "public", False)
        and not getattr(result, "security_claim", True)
    ):
        return ReproductionResult(
            attempted=True,
            status="instance_solved",
            success=True,
            score=IMPLEMENTATION_SECURITY_INSTANCE_REPRODUCTION_SCORE,
            warnings=[
                "Verified a public JSON-only toy binary-size fixture without "
                "executing artifacts; this is reproducibility plumbing, not "
                "a binary-size, performance, conformance, side-channel, or "
                "security claim."
            ],
        )
    return ReproductionResult(
        attempted=True,
        status="failed",
        success=False,
        warnings=[
            "IMPLEMENTATION_SECURITY toy binary-size fixture did not match the "
            "expected public no-execution plan."
        ],
    )


def _reproduce_memory_benchmark(
    plan: AttackPlan,
    operator: AttackOperator,
    result: ToyBenchmarkFixtureResult,
) -> ReproductionResult:
    expected_fields = (
        "stack_bytes",
        "heap_bytes",
        "code_bytes",
        "max_stack_bytes",
        "max_heap_bytes",
        "max_code_bytes",
    )
    if (
        getattr(result, "verified", False)
        and getattr(result, "target_name", None) == plan.target.name
        and getattr(result, "suite", None) == operator.params.get("suite")
        and getattr(result, "metric", None) == operator.params.get("metric")
        and getattr(result, "model", None) == operator.params.get("model")
        and all(
            getattr(result, field, None) == operator.params.get(field)
            for field in expected_fields
        )
        and not getattr(result, "artifact_execution", True)
        and getattr(result, "public", False)
        and not getattr(result, "security_claim", True)
    ):
        return ReproductionResult(
            attempted=True,
            status="instance_solved",
            success=True,
            score=IMPLEMENTATION_SECURITY_INSTANCE_REPRODUCTION_SCORE,
            warnings=[
                "Verified a public JSON-only toy memory-footprint fixture "
                "without executing artifacts; this is reproducibility plumbing, "
                "not a memory-usage, performance, conformance, side-channel, "
                "or security claim."
            ],
        )
    return ReproductionResult(
        attempted=True,
        status="failed",
        success=False,
        warnings=[
            "IMPLEMENTATION_SECURITY toy memory fixture did not match the "
            "expected public no-execution plan."
        ],
    )


def _reproduce_stack_usage_benchmark(
    plan: AttackPlan,
    operator: AttackOperator,
    result: ToyBenchmarkFixtureResult,
) -> ReproductionResult:
    expected_fields = (
        "stack_samples",
        "max_stack_bytes",
    )
    if (
        getattr(result, "verified", False)
        and getattr(result, "target_name", None) == plan.target.name
        and getattr(result, "suite", None) == operator.params.get("suite")
        and getattr(result, "metric", None) == operator.params.get("metric")
        and getattr(result, "model", None) == operator.params.get("model")
        and all(
            getattr(result, field, None) == operator.params.get(field)
            for field in expected_fields
        )
        and not getattr(result, "artifact_execution", True)
        and getattr(result, "public", False)
        and not getattr(result, "security_claim", True)
    ):
        return ReproductionResult(
            attempted=True,
            status="instance_solved",
            success=True,
            score=IMPLEMENTATION_SECURITY_INSTANCE_REPRODUCTION_SCORE,
            warnings=[
                "Verified a public JSON-only toy stack-usage fixture without "
                "executing artifacts; this is reproducibility plumbing, not "
                "a stack-usage, performance, conformance, side-channel, or "
                "security claim."
            ],
        )
    return ReproductionResult(
        attempted=True,
        status="failed",
        success=False,
        warnings=[
            "IMPLEMENTATION_SECURITY toy stack-usage fixture did not match the "
            "expected public no-execution plan."
        ],
    )


def _is_timing_plan(plan: AttackPlan) -> bool:
    return any(operator.type == "constant_time_check" for operator in plan.operators)


def _is_benchmark_plan(plan: AttackPlan) -> bool:
    return any(operator.type == "benchmark_harness" for operator in plan.operators)


def _fixture_root_parts_for_plan(plan: AttackPlan) -> tuple[str, ...]:
    if _is_timing_plan(plan):
        return _TIMING_FIXTURE_ROOT_PARTS
    if _is_benchmark_plan(plan):
        return _BENCHMARK_FIXTURE_ROOT_PARTS
    return _KAT_FIXTURE_ROOT_PARTS


def _resolve_fixture_path(
    value: str,
    root_parts: tuple[str, ...],
) -> tuple[Path | None, list[str]]:
    return resolve_public_fixture_path(
        value,
        repo_root=ROOT,
        package_fixture_dir=PACKAGE_FIXTURES,
        root_parts=root_parts,
        family_label="IMPLEMENTATION_SECURITY",
    )


def _is_scoped_fixture_path(path: Path, root_parts: tuple[str, ...]) -> bool:
    return is_scoped_public_fixture_path(path, root_parts)


def _fixture_scope(root_parts: tuple[str, ...]) -> str:
    return "/".join(root_parts) + "/"
