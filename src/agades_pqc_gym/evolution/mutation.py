from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.target import SupportLevel, TargetFamily
from agades_pqc_gym.core.trace_record import TraceRecord
from agades_pqc_gym.evolution.archive import EliteRecord, EvolutionArchive
from agades_pqc_gym.families.code_based.isd_estimator import (
    BJMM_TOY_VARIANT,
    DUMER_TOY_VARIANT,
    LEE_BRICKELL_TOY_VARIANT,
    PRANGE_TOY_VARIANT,
    STERN_TOY_VARIANT,
)
from agades_pqc_gym.families.hash_based.bound_estimator import (
    TOY_PREIMAGE_BOUND_MODEL,
)
from agades_pqc_gym.families.implementation_security.kat_estimator import (
    TOY_KAT_MODEL,
)
from agades_pqc_gym.families.isogeny_historical.path_estimator import (
    TOY_ISOGENY_CASES,
)
from agades_pqc_gym.families.multivariate.mq_estimator import (
    TOY_MQ_DEGREE_BOUND_MODEL,
    TOY_MQ_HYBRID_MODEL,
    TOY_MQ_MODEL,
    field_order_from_notation,
)
from agades_pqc_gym.validators.static import validate_attack_plan

CANDIDATE_MUTATION_BATCH_SCHEMA = "agades.pqc.candidate_mutation_batch.v1"
_BETA_DELTAS = (-4, 4)
_BLOCK_SIZE_DELTAS = (-1, 1)
_ZETA_DELTAS = (-1, 1)
_CODE_BASED_PRANGE_WEIGHT_DELTAS = (-1, 1)
_CODE_BASED_P_DELTAS = (-1, 1)
_CODE_BASED_ELL_DELTAS = (-1, 1)
_MULTIVARIATE_VARIABLE_DELTAS = (-1, 1)
_MULTIVARIATE_EQUATION_DELTAS = (-1, 1)
_MULTIVARIATE_GUESSED_VARIABLE_DELTAS = (-1, 1)
_MULTIVARIATE_DEGREE_BOUND_DELTAS = (-1, 1)
_HASH_PREIMAGE_DIGEST_BITS_DELTAS = (-8, 8)
_IMPLEMENTATION_SECURITY_VECTOR_COUNT_DELTAS = (-1, 1)
_ISOGENY_HISTORICAL_WALK_DELTAS = (-1, 1)
_ISOGENY_HISTORICAL_BRANCHING_DELTAS = (-1, 1)
_LATTICE_MUTATION_FAMILIES = {TargetFamily.LWE, TargetFamily.MLWE}
_MUTATION_FAMILIES = {
    *_LATTICE_MUTATION_FAMILIES,
    TargetFamily.CODE_BASED,
    TargetFamily.HASH_BASED,
    TargetFamily.IMPLEMENTATION_SECURITY,
    TargetFamily.ISOGENY_HISTORICAL,
    TargetFamily.MULTIVARIATE,
}


class CandidateMutationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: str
    parent_attack_plan_id: str
    parent_candidate_id: str | None = None
    parent_trace_id: str | None = None
    generation: int = Field(ge=1)
    mutation_summary: str
    attack_plan: AttackPlan


class SkippedMutationSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attack_plan_id: str
    target_family: str
    reason: str


class CandidateMutationBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = CANDIDATE_MUTATION_BATCH_SCHEMA
    run_id: str
    summary: dict[str, int]
    candidates: list[CandidateMutationRecord]
    skipped: list[SkippedMutationSource]


def build_candidate_mutation_batch(
    plans: Iterable[AttackPlan],
    *,
    run_id: str,
    generation: int = 1,
    max_mutations_per_plan: int = 4,
) -> CandidateMutationBatch:
    if generation < 1:
        raise ValueError("Candidate mutation generation must be >= 1.")
    if max_mutations_per_plan < 1:
        raise ValueError("max_mutations_per_plan must be >= 1.")

    source_plans = list(plans)
    candidates: list[CandidateMutationRecord] = []
    skipped: list[SkippedMutationSource] = []

    for plan in source_plans:
        mutations = _mutations_for_plan(
            plan,
            generation=generation,
            max_mutations=max_mutations_per_plan,
        )
        if not mutations:
            skipped.append(
                SkippedMutationSource(
                    attack_plan_id=plan.attack_plan_id,
                    target_family=plan.target.family.value,
                    reason=_skip_reason_for_plan(plan),
                )
            )
            continue
        candidates.extend(mutations)

    return CandidateMutationBatch(
        run_id=run_id,
        summary={
            "candidate_count": len(candidates),
            "source_count": len(source_plans),
            "skipped_count": len(skipped),
        },
        candidates=candidates,
        skipped=skipped,
    )


def write_candidate_mutation_batch(
    plans: Iterable[AttackPlan],
    out_dir: Path,
    *,
    run_id: str,
    generation: int = 1,
    max_mutations_per_plan: int = 4,
) -> CandidateMutationBatch:
    batch = build_candidate_mutation_batch(
        plans,
        run_id=run_id,
        generation=generation,
        max_mutations_per_plan=max_mutations_per_plan,
    )
    return _write_candidate_mutation_batch(batch, out_dir)


def build_archive_candidate_mutation_batch(
    archive: EvolutionArchive,
    source_records: Iterable[TraceRecord],
    *,
    run_id: str,
    generation: int | None = None,
    max_mutations_per_elite: int = 4,
) -> CandidateMutationBatch:
    resolved_generation = _resolve_archive_generation(archive, generation)
    if max_mutations_per_elite < 1:
        raise ValueError("max_mutations_per_elite must be >= 1.")

    records_by_trace_id = {record.trace_id: record for record in source_records}
    candidates: list[CandidateMutationRecord] = []
    skipped: list[SkippedMutationSource] = []

    for elite in archive.elites:
        source_record = _source_record_for_elite(elite, records_by_trace_id)
        mutations = _mutations_for_plan(
            source_record.attack_plan,
            generation=resolved_generation,
            max_mutations=max_mutations_per_elite,
            parent_candidate_id=elite.candidate_id,
            parent_trace_id=elite.trace_id,
        )
        if not mutations:
            skipped.append(
                SkippedMutationSource(
                    attack_plan_id=source_record.attack_plan.attack_plan_id,
                    target_family=source_record.attack_plan.target.family.value,
                    reason=_skip_reason_for_plan(source_record.attack_plan),
                )
            )
            continue
        candidates.extend(mutations)

    return CandidateMutationBatch(
        run_id=run_id,
        summary={
            "candidate_count": len(candidates),
            "source_count": len(archive.elites),
            "skipped_count": len(skipped),
        },
        candidates=candidates,
        skipped=skipped,
    )


def write_archive_candidate_mutation_batch(
    archive: EvolutionArchive,
    source_records: Iterable[TraceRecord],
    out_dir: Path,
    *,
    run_id: str,
    generation: int | None = None,
    max_mutations_per_elite: int = 4,
) -> CandidateMutationBatch:
    batch = build_archive_candidate_mutation_batch(
        archive,
        source_records,
        run_id=run_id,
        generation=generation,
        max_mutations_per_elite=max_mutations_per_elite,
    )
    return _write_candidate_mutation_batch(batch, out_dir)


def _write_candidate_mutation_batch(
    batch: CandidateMutationBatch,
    out_dir: Path,
) -> CandidateMutationBatch:
    plans_dir = out_dir / "plans"
    plan_paths = {
        candidate.candidate_id: plans_dir / f"{candidate.candidate_id}.json"
        for candidate in batch.candidates
    }

    if plans_dir.exists():
        expected = {path.name for path in plan_paths.values()}
        stale = sorted(
            path.name
            for path in plans_dir.glob("*.json")
            if path.name not in expected
        )
        if stale:
            raise ValueError(
                "Refusing to write candidate mutations into a plans directory "
                f"with stale JSON files: {', '.join(stale)}."
            )

    plans_dir.mkdir(parents=True, exist_ok=True)
    for candidate in batch.candidates:
        plan_paths[candidate.candidate_id].write_text(
            candidate.attack_plan.model_dump_json(indent=2) + "\n",
            encoding="utf-8",
        )

    manifest = _manifest_for_batch(batch, plan_paths, out_dir)
    (out_dir / "mutation_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return batch


def _resolve_archive_generation(
    archive: EvolutionArchive,
    generation: int | None,
) -> int:
    if generation is not None:
        if generation < 1:
            raise ValueError("Candidate mutation generation must be >= 1.")
        return generation
    if not archive.elites:
        return 1
    return max(elite.generation for elite in archive.elites) + 1


def _source_record_for_elite(
    elite: EliteRecord,
    records_by_trace_id: dict[str, TraceRecord],
) -> TraceRecord:
    source_record = records_by_trace_id.get(elite.trace_id)
    if source_record is None:
        raise ValueError(
            f"Archive elite {elite.candidate_id} is missing from source trace."
        )
    if source_record.candidate_id != elite.candidate_id:
        raise ValueError(
            f"Archive elite {elite.candidate_id} points to trace {elite.trace_id}, "
            f"but source trace candidate is {source_record.candidate_id}."
        )
    if source_record.attack_plan.attack_plan_id != elite.attack_plan_id:
        raise ValueError(
            f"Archive elite {elite.candidate_id} points to AttackPlan "
            f"{elite.attack_plan_id}, but source trace contains "
            f"{source_record.attack_plan.attack_plan_id}."
        )
    return source_record


def _skip_reason_for_plan(plan: AttackPlan) -> str:
    family = plan.target.family.value
    if plan.target.support_level is SupportLevel.SCHEMA_ONLY:
        return f"schema-only mutation skipped for {family}"
    if _plan_is_fixture_bound(plan):
        return f"fixture-bound mutation skipped for {family}"
    return f"no reviewed mutation rules for {family}"


def _plan_is_fixture_bound(plan: AttackPlan) -> bool:
    return (
        plan.constraints.require_reproducibility_on_downscaled_instances
        or plan.constraints.downscaled_reproduction_fixture is not None
    )


def _mutations_for_plan(
    plan: AttackPlan,
    *,
    generation: int,
    max_mutations: int,
    parent_candidate_id: str | None = None,
    parent_trace_id: str | None = None,
) -> list[CandidateMutationRecord]:
    if (
        plan.target.support_level is SupportLevel.SCHEMA_ONLY
        or _plan_is_fixture_bound(plan)
    ):
        return []
    if plan.target.family not in _MUTATION_FAMILIES:
        return []

    mutations: list[CandidateMutationRecord] = []
    for target_updates, mutation_id, mutation_summary in _target_mutations_for_plan(
        plan
    ):
        mutations.append(
            _candidate_from_target_mutation(
                plan,
                generation=generation,
                mutation_id=mutation_id,
                mutation_summary=mutation_summary,
                target_updates=target_updates,
                parent_candidate_id=parent_candidate_id,
                parent_trace_id=parent_trace_id,
            )
        )
        if len(mutations) >= max_mutations:
            return mutations

    mutatable_operator_indexes = [
        index
        for index, operator in enumerate(plan.operators)
        if _operator_param_mutations(plan, index)
    ]
    use_operator_prefix = len(mutatable_operator_indexes) > 1

    for operator_index in mutatable_operator_indexes:
        for param_name, new_value, local_mutation_id in _operator_param_mutations(
            plan,
            operator_index,
        ):
            mutation_id = _mutation_id(
                operator_index=operator_index,
                local_mutation_id=local_mutation_id,
                use_operator_prefix=use_operator_prefix,
            )
            old_value = plan.operators[operator_index].params[param_name]
            mutation_summary = _mutation_summary(
                operator_index=operator_index,
                param_name=param_name,
                old_value=old_value,
                new_value=new_value,
            )
            mutations.append(
                _candidate_from_mutation(
                    plan,
                    generation=generation,
                    mutation_id=mutation_id,
                    mutation_summary=mutation_summary,
                    operator_index=operator_index,
                    param_name=param_name,
                    param_value=new_value,
                    parent_candidate_id=parent_candidate_id,
                    parent_trace_id=parent_trace_id,
                )
            )
            if len(mutations) >= max_mutations:
                return mutations

    return mutations


def _target_mutations_for_plan(
    plan: AttackPlan,
) -> list[tuple[dict[str, Any], str, str]]:
    if plan.target.family is TargetFamily.CODE_BASED:
        return _code_based_target_mutations(plan)
    if plan.target.family is TargetFamily.MULTIVARIATE:
        return _multivariate_target_mutations(plan)
    if plan.target.family is TargetFamily.HASH_BASED:
        return _hash_based_target_mutations(plan)
    return []


def _code_based_target_mutations(
    plan: AttackPlan,
) -> list[tuple[dict[str, Any], str, str]]:
    if plan.target.support_level is not SupportLevel.IMPLEMENTED:
        return []
    if _plan_is_fixture_bound(plan):
        return []
    if len(plan.operators) != 1:
        return []

    operator = plan.operators[0]
    if operator.type != "information_set_decoding":
        return []
    if operator.params.get("variant") != PRANGE_TOY_VARIANT:
        return []

    n = plan.target.n
    k = plan.target.k
    w = plan.target.w
    if (
        not isinstance(n, int)
        or isinstance(n, bool)
        or not isinstance(k, int)
        or isinstance(k, bool)
        or not isinstance(w, int)
        or isinstance(w, bool)
    ):
        return []
    if k >= n:
        return []

    expected_name = f"toy_syndrome_{n}_{k}_w{w}"
    if plan.target.name != expected_name:
        return []

    redundancy = n - k
    mutations: list[tuple[dict[str, Any], str, str]] = []
    for delta in _CODE_BASED_PRANGE_WEIGHT_DELTAS:
        new_w = w + delta
        if new_w <= 0 or new_w >= n or new_w > redundancy or new_w == w:
            continue
        target_updates: dict[str, Any] = {
            "w": new_w,
            "claimed_security_bits": None,
            "name": f"toy_syndrome_{n}_{k}_w{new_w}",
        }
        if not _target_values_valid(plan, target_updates):
            continue
        direction = "plus" if delta > 0 else "minus"
        mutation_id = f"target_w_{direction}_{abs(delta)}"
        mutation_summary = _target_mutation_summary(plan, target_updates)
        mutations.append((target_updates, mutation_id, mutation_summary))
    return mutations


def _hash_based_target_mutations(
    plan: AttackPlan,
) -> list[tuple[dict[str, Any], str, str]]:
    if plan.target.support_level is not SupportLevel.IMPLEMENTED:
        return []
    if _plan_is_fixture_bound(plan):
        return []
    if len(plan.operators) != 1:
        return []

    operator = plan.operators[0]
    if operator.type != "security_bound_check":
        return []
    if operator.params.get("bound_model") != TOY_PREIMAGE_BOUND_MODEL:
        return []

    digest_bits = plan.target.n
    if not isinstance(digest_bits, int) or isinstance(digest_bits, bool):
        return []

    mutations: list[tuple[dict[str, Any], str, str]] = []
    for delta in _HASH_PREIMAGE_DIGEST_BITS_DELTAS:
        new_digest_bits = digest_bits + delta
        if new_digest_bits <= 0 or new_digest_bits == digest_bits:
            continue
        target_updates: dict[str, Any] = {"n": new_digest_bits}
        if plan.target.claimed_security_bits is not None:
            target_updates["claimed_security_bits"] = float(new_digest_bits)
        current_name = plan.target.name
        expected_name = f"toy_hash_preimage_{digest_bits}"
        if current_name == expected_name:
            target_updates["name"] = f"toy_hash_preimage_{new_digest_bits}"
        if not _target_values_valid(plan, target_updates):
            continue
        direction = "plus" if delta > 0 else "minus"
        mutation_id = f"target_n_{direction}_{abs(delta)}"
        mutation_summary = _target_mutation_summary(plan, target_updates)
        mutations.append((target_updates, mutation_id, mutation_summary))
    return mutations


def _multivariate_target_mutations(
    plan: AttackPlan,
) -> list[tuple[dict[str, Any], str, str]]:
    if plan.target.support_level is not SupportLevel.IMPLEMENTED:
        return []
    if _plan_is_fixture_bound(plan):
        return []
    if len(plan.operators) != 1:
        return []

    operator = plan.operators[0]
    if operator.type != "groebner_basis":
        return []
    if operator.params.get("model") != TOY_MQ_MODEL:
        return []

    variables = plan.target.variables
    equations = plan.target.equations
    field = plan.target.field
    if (
        not isinstance(variables, int)
        or isinstance(variables, bool)
        or not isinstance(equations, int)
        or isinstance(equations, bool)
        or field is None
    ):
        return []
    try:
        field_order = field_order_from_notation(field)
    except ValueError:
        return []

    expected_name = f"toy_mq_gf{field_order}_v{variables}_e{equations}"
    if plan.target.name != expected_name:
        return []

    mutations: list[tuple[dict[str, Any], str, str]] = []
    mutations.extend(
        _multivariate_dimension_mutations(
            plan=plan,
            field_order=field_order,
            variables=variables,
            equations=equations,
            target_field="variables",
            deltas=_MULTIVARIATE_VARIABLE_DELTAS,
        )
    )
    mutations.extend(
        _multivariate_dimension_mutations(
            plan=plan,
            field_order=field_order,
            variables=variables,
            equations=equations,
            target_field="equations",
            deltas=_MULTIVARIATE_EQUATION_DELTAS,
        )
    )
    return mutations


def _multivariate_dimension_mutations(
    *,
    plan: AttackPlan,
    field_order: int,
    variables: int,
    equations: int,
    target_field: str,
    deltas: tuple[int, ...],
) -> list[tuple[dict[str, Any], str, str]]:
    current_value = variables if target_field == "variables" else equations
    mutations: list[tuple[dict[str, Any], str, str]] = []
    for delta in deltas:
        new_value = current_value + delta
        if new_value <= 0 or new_value == current_value:
            continue
        new_variables = new_value if target_field == "variables" else variables
        new_equations = new_value if target_field == "equations" else equations
        target_updates: dict[str, Any] = {
            target_field: new_value,
            "claimed_security_bits": None,
            "name": f"toy_mq_gf{field_order}_v{new_variables}_e{new_equations}",
        }
        if not _target_values_valid(plan, target_updates):
            continue
        direction = "plus" if delta > 0 else "minus"
        mutation_id = f"target_{target_field}_{direction}_{abs(delta)}"
        mutation_summary = _target_mutation_summary(plan, target_updates)
        mutations.append((target_updates, mutation_id, mutation_summary))
    return mutations


def _operator_param_mutations(
    plan: AttackPlan,
    operator_index: int,
) -> list[tuple[str, int, str]]:
    if plan.target.family in _LATTICE_MUTATION_FAMILIES:
        return _lattice_operator_param_mutations(plan, operator_index)
    if plan.target.family is TargetFamily.CODE_BASED:
        return _code_based_operator_param_mutations(plan, operator_index)
    if plan.target.family is TargetFamily.MULTIVARIATE:
        return _multivariate_operator_param_mutations(plan, operator_index)
    if plan.target.family is TargetFamily.IMPLEMENTATION_SECURITY:
        return _implementation_security_operator_param_mutations(
            plan,
            operator_index,
        )
    if plan.target.family is TargetFamily.ISOGENY_HISTORICAL:
        return _isogeny_historical_operator_param_mutations(plan, operator_index)
    return []


def _lattice_operator_param_mutations(
    plan: AttackPlan,
    operator_index: int,
) -> list[tuple[str, int, str]]:
    operator = plan.operators[operator_index]
    mutations: list[tuple[str, int, str]] = []

    q_prime = operator.params.get("q_prime")
    if isinstance(q_prime, int) and not isinstance(q_prime, bool):
        mutations.extend(_q_prime_mutations(plan, q_prime))

    beta = operator.params.get("beta")
    if isinstance(beta, int) and not isinstance(beta, bool):
        mutations.extend(
            _integer_delta_mutations(
                param_name="beta",
                current_value=beta,
                deltas=_BETA_DELTAS,
            )
        )

    block_size = operator.params.get("block_size")
    if isinstance(block_size, int) and not isinstance(block_size, bool):
        mutations.extend(
            _integer_delta_mutations(
                param_name="block_size",
                current_value=block_size,
                deltas=_BLOCK_SIZE_DELTAS,
            )
        )

    zeta = operator.params.get("zeta")
    if isinstance(zeta, int) and not isinstance(zeta, bool):
        mutations.extend(
            _integer_delta_mutations(
                param_name="zeta",
                current_value=zeta,
                deltas=_ZETA_DELTAS,
            )
        )

    return mutations


def _code_based_operator_param_mutations(
    plan: AttackPlan,
    operator_index: int,
) -> list[tuple[str, int, str]]:
    if plan.target.support_level is not SupportLevel.IMPLEMENTED:
        return []

    operator = plan.operators[operator_index]
    if operator.type != "information_set_decoding":
        return []

    variant = operator.params.get("variant")
    mutations: list[tuple[str, int, str]] = []
    if variant in {
        BJMM_TOY_VARIANT,
        DUMER_TOY_VARIANT,
        LEE_BRICKELL_TOY_VARIANT,
        STERN_TOY_VARIANT,
    }:
        mutations.extend(
            _validated_integer_delta_mutations(
                plan=plan,
                operator_index=operator_index,
                param_name="p",
                current_value=operator.params.get("p"),
                deltas=_CODE_BASED_P_DELTAS,
            )
        )

    if variant in {BJMM_TOY_VARIANT, DUMER_TOY_VARIANT}:
        mutations.extend(
            _validated_integer_delta_mutations(
                plan=plan,
                operator_index=operator_index,
                param_name="ell",
                current_value=operator.params.get("ell"),
                deltas=_CODE_BASED_ELL_DELTAS,
            )
        )

    if variant == BJMM_TOY_VARIANT:
        mutations.extend(
            _validated_halving_doubling_mutations(
                plan=plan,
                operator_index=operator_index,
                param_name="representation_count",
                current_value=operator.params.get("representation_count"),
            )
        )

    return mutations


def _validated_integer_delta_mutations(
    *,
    plan: AttackPlan,
    operator_index: int,
    param_name: str,
    current_value: object,
    deltas: tuple[int, ...],
) -> list[tuple[str, int, str]]:
    if not isinstance(current_value, int) or isinstance(current_value, bool):
        return []

    mutations: list[tuple[str, int, str]] = []
    for delta in deltas:
        new_value = current_value + delta
        if new_value < 0 or new_value == current_value:
            continue
        if not _operator_param_value_valid(plan, operator_index, param_name, new_value):
            continue
        direction = "plus" if delta > 0 else "minus"
        mutations.append(
            (
                param_name,
                new_value,
                f"{param_name}_{direction}_{abs(delta)}",
            )
        )
    return mutations


def _multivariate_operator_param_mutations(
    plan: AttackPlan,
    operator_index: int,
) -> list[tuple[str, int, str]]:
    if plan.target.support_level is not SupportLevel.IMPLEMENTED:
        return []
    if _plan_is_fixture_bound(plan):
        return []

    operator = plan.operators[operator_index]
    if operator.type != "groebner_basis":
        return []

    model = operator.params.get("model")
    if model == TOY_MQ_HYBRID_MODEL:
        return _validated_integer_delta_mutations(
            plan=plan,
            operator_index=operator_index,
            param_name="guessed_variables",
            current_value=operator.params.get("guessed_variables"),
            deltas=_MULTIVARIATE_GUESSED_VARIABLE_DELTAS,
        )
    if model == TOY_MQ_DEGREE_BOUND_MODEL:
        return _validated_integer_delta_mutations(
            plan=plan,
            operator_index=operator_index,
            param_name="degree_bound",
            current_value=operator.params.get("degree_bound"),
            deltas=_MULTIVARIATE_DEGREE_BOUND_DELTAS,
        )
    return []


def _implementation_security_operator_param_mutations(
    plan: AttackPlan,
    operator_index: int,
) -> list[tuple[str, int, str]]:
    if plan.target.support_level is not SupportLevel.IMPLEMENTED:
        return []
    if _plan_is_fixture_bound(plan):
        return []

    operator = plan.operators[operator_index]
    if operator.type != "kat_conformance":
        return []
    if operator.params.get("model") != TOY_KAT_MODEL:
        return []

    return _validated_integer_delta_mutations(
        plan=plan,
        operator_index=operator_index,
        param_name="vector_count",
        current_value=operator.params.get("vector_count"),
        deltas=_IMPLEMENTATION_SECURITY_VECTOR_COUNT_DELTAS,
    )


def _isogeny_historical_operator_param_mutations(
    plan: AttackPlan,
    operator_index: int,
) -> list[tuple[str, int, str]]:
    if plan.target.support_level is not SupportLevel.IMPLEMENTED:
        return []
    if _plan_is_fixture_bound(plan):
        return []

    operator = plan.operators[operator_index]
    if operator.type != "historical_isogeny_reconstruction":
        return []
    if operator.params.get("case") not in TOY_ISOGENY_CASES:
        return []

    mutations: list[tuple[str, int, str]] = []
    mutations.extend(
        _validated_integer_delta_mutations(
            plan=plan,
            operator_index=operator_index,
            param_name="walk_length",
            current_value=operator.params.get("walk_length"),
            deltas=_ISOGENY_HISTORICAL_WALK_DELTAS,
        )
    )
    mutations.extend(
        _validated_integer_delta_mutations(
            plan=plan,
            operator_index=operator_index,
            param_name="branching_factor",
            current_value=operator.params.get("branching_factor"),
            deltas=_ISOGENY_HISTORICAL_BRANCHING_DELTAS,
        )
    )
    return mutations


def _operator_param_value_valid(
    plan: AttackPlan,
    operator_index: int,
    param_name: str,
    new_value: int,
) -> bool:
    data = plan.model_dump(mode="json")
    data["operators"][operator_index]["params"][param_name] = new_value
    try:
        candidate = AttackPlan.model_validate(data)
    except ValueError:
        return False
    return validate_attack_plan(candidate).valid


def _target_values_valid(plan: AttackPlan, target_updates: dict[str, Any]) -> bool:
    data = plan.model_dump(mode="json")
    data["target"].update(target_updates)
    try:
        candidate = AttackPlan.model_validate(data)
    except ValueError:
        return False
    return validate_attack_plan(candidate).valid


def _target_mutation_summary(
    plan: AttackPlan,
    target_updates: dict[str, Any],
) -> str:
    parts: list[str] = []
    for field_name, new_value in target_updates.items():
        old_value = getattr(plan.target, field_name)
        if old_value != new_value:
            parts.append(f"target.{field_name}: {old_value} -> {new_value}")
    return "; ".join(parts)


def _validated_halving_doubling_mutations(
    *,
    plan: AttackPlan,
    operator_index: int,
    param_name: str,
    current_value: object,
) -> list[tuple[str, int, str]]:
    if not isinstance(current_value, int) or isinstance(current_value, bool):
        return []

    candidates = [
        (current_value // 2, f"{param_name}_div_2"),
        (current_value * 2, f"{param_name}_times_2"),
    ]
    mutations: list[tuple[str, int, str]] = []
    for new_value, mutation_id in candidates:
        if new_value <= 0 or new_value == current_value:
            continue
        if not _operator_param_value_valid(plan, operator_index, param_name, new_value):
            continue
        mutations.append((param_name, new_value, mutation_id))
    return mutations


def _integer_delta_mutations(
    *,
    param_name: str,
    current_value: int,
    deltas: tuple[int, ...],
) -> list[tuple[str, int, str]]:
    mutations: list[tuple[str, int, str]] = []
    for delta in deltas:
        new_value = current_value + delta
        if new_value <= 0 or new_value == current_value:
            continue
        direction = "plus" if delta > 0 else "minus"
        mutations.append(
            (
                param_name,
                new_value,
                f"{param_name}_{direction}_{abs(delta)}",
            )
        )
    return mutations


def _q_prime_mutations(
    plan: AttackPlan,
    current_value: int,
) -> list[tuple[str, int, str]]:
    target_q = plan.target.q
    candidates = [
        ("q_prime", current_value // 2, "q_prime_div_2"),
        ("q_prime", current_value * 2, "q_prime_times_2"),
    ]
    mutations: list[tuple[str, int, str]] = []
    for param_name, raw_value, mutation_id in candidates:
        new_value = raw_value
        if target_q is not None and target_q > 2:
            new_value = min(new_value, target_q - 1)
        if new_value <= 1 or new_value == current_value:
            continue
        mutations.append((param_name, new_value, mutation_id))
    return mutations


def _candidate_from_mutation(
    plan: AttackPlan,
    *,
    generation: int,
    mutation_id: str,
    mutation_summary: str,
    operator_index: int,
    param_name: str,
    param_value: int,
    parent_candidate_id: str | None = None,
    parent_trace_id: str | None = None,
) -> CandidateMutationRecord:
    data = plan.model_dump(mode="json")
    candidate_id = _safe_identifier(
        f"{plan.attack_plan_id}__g{generation}__{mutation_id}"
    )
    data["attack_plan_id"] = candidate_id
    data["operators"][operator_index]["params"][param_name] = param_value
    data["claims"] = {
        "estimated_time_bits": None,
        "estimated_memory_bits": None,
        "success_probability": None,
        "external_claim": False,
        "source": None,
    }
    data["metadata"] = {
        **data["metadata"],
        "created_by": "mutation_batch",
        "public": False,
        "notes": _mutation_notes(plan, mutation_summary),
    }

    attack_plan = AttackPlan.model_validate(data)
    validation = validate_attack_plan(attack_plan)
    if not validation.valid:
        raise ValueError(
            f"Generated mutation {candidate_id} failed validation: "
            f"{'; '.join(validation.errors)}"
        )
    return CandidateMutationRecord(
        candidate_id=candidate_id,
        parent_attack_plan_id=plan.attack_plan_id,
        parent_candidate_id=parent_candidate_id,
        parent_trace_id=parent_trace_id,
        generation=generation,
        mutation_summary=mutation_summary,
        attack_plan=attack_plan,
    )


def _candidate_from_target_mutation(
    plan: AttackPlan,
    *,
    generation: int,
    mutation_id: str,
    mutation_summary: str,
    target_updates: dict[str, Any],
    parent_candidate_id: str | None = None,
    parent_trace_id: str | None = None,
) -> CandidateMutationRecord:
    data = plan.model_dump(mode="json")
    candidate_id = _safe_identifier(
        f"{plan.attack_plan_id}__g{generation}__{mutation_id}"
    )
    data["attack_plan_id"] = candidate_id
    data["target"].update(target_updates)
    data["claims"] = {
        "estimated_time_bits": None,
        "estimated_memory_bits": None,
        "success_probability": None,
        "external_claim": False,
        "source": None,
    }
    data["metadata"] = {
        **data["metadata"],
        "created_by": "mutation_batch",
        "public": False,
        "notes": _mutation_notes(plan, mutation_summary),
    }

    attack_plan = AttackPlan.model_validate(data)
    validation = validate_attack_plan(attack_plan)
    if not validation.valid:
        raise ValueError(
            f"Generated mutation {candidate_id} failed validation: "
            f"{'; '.join(validation.errors)}"
        )
    return CandidateMutationRecord(
        candidate_id=candidate_id,
        parent_attack_plan_id=plan.attack_plan_id,
        parent_candidate_id=parent_candidate_id,
        parent_trace_id=parent_trace_id,
        generation=generation,
        mutation_summary=mutation_summary,
        attack_plan=attack_plan,
    )


def _mutation_id(
    *,
    operator_index: int,
    local_mutation_id: str,
    use_operator_prefix: bool,
) -> str:
    prefix = f"operator_{operator_index}_" if use_operator_prefix else ""
    return f"{prefix}{local_mutation_id}"


def _mutation_summary(
    *,
    operator_index: int,
    param_name: str,
    old_value: int,
    new_value: int,
) -> str:
    return f"operator[{operator_index}].params.{param_name}: {old_value} -> {new_value}"


def _mutation_notes(plan: AttackPlan, mutation_summary: str) -> str:
    source_notes = plan.metadata.notes.strip()
    prefix = (
        f"Private deterministic JSON AttackPlan mutation of {plan.attack_plan_id}: "
        f"{mutation_summary}. Not a security claim."
    )
    if not source_notes:
        return prefix
    return f"{prefix} Source notes: {source_notes}"


def _manifest_for_batch(
    batch: CandidateMutationBatch,
    plan_paths: dict[str, Path],
    out_dir: Path,
) -> dict[str, Any]:
    return {
        "schema_version": batch.schema_version,
        "run_id": batch.run_id,
        "summary": batch.summary,
        "safety": {
            "arbitrary_code_execution": False,
            "generated_candidates_public": False,
            "publishes_private_candidates": False,
            "security_claim": False,
        },
        "candidates": [
            _manifest_candidate_entry(candidate, plan_paths, out_dir)
            for candidate in batch.candidates
        ],
        "skipped": [
            skipped.model_dump(mode="json") for skipped in batch.skipped
        ],
    }


def _manifest_candidate_entry(
    candidate: CandidateMutationRecord,
    plan_paths: dict[str, Path],
    out_dir: Path,
) -> dict[str, Any]:
    entry = {
        "candidate_id": candidate.candidate_id,
        "parent_attack_plan_id": candidate.parent_attack_plan_id,
        "generation": candidate.generation,
        "mutation_summary": candidate.mutation_summary,
        "target_family": candidate.attack_plan.target.family.value,
        "path": plan_paths[candidate.candidate_id].relative_to(out_dir).as_posix(),
    }
    if candidate.parent_candidate_id is not None:
        entry["parent_candidate_id"] = candidate.parent_candidate_id
    if candidate.parent_trace_id is not None:
        entry["parent_trace_id"] = candidate.parent_trace_id
    return entry


def _safe_identifier(value: str) -> str:
    safe = "".join(
        character if character.isalnum() or character in {"_", "-"} else "_"
        for character in value
    )
    return safe.strip("_") or "candidate"
