from __future__ import annotations

import json
from pathlib import Path

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.evolution.archive import build_evolution_archive
from agades_pqc_gym.evolution.mutation import (
    CANDIDATE_MUTATION_BATCH_SCHEMA,
    build_archive_candidate_mutation_batch,
    build_candidate_mutation_batch,
    write_archive_candidate_mutation_batch,
    write_candidate_mutation_batch,
)
from agades_pqc_gym.traces.schema import TraceRecord
from agades_pqc_gym.validators.static import validate_attack_plan


def test_build_candidate_mutation_batch_generates_private_lattice_mutations() -> None:
    plan = _plan("examples/attack_plans/lattice_primal_usvp_toy.json")

    batch = build_candidate_mutation_batch(
        [plan],
        run_id="unit-mutation",
        generation=1,
        max_mutations_per_plan=2,
    )

    assert batch.schema_version == CANDIDATE_MUTATION_BATCH_SCHEMA
    assert batch.summary == {
        "candidate_count": 2,
        "source_count": 1,
        "skipped_count": 0,
    }
    assert [candidate.candidate_id for candidate in batch.candidates] == [
        "lattice_primal_usvp_toy_v1__g1__beta_minus_4",
        "lattice_primal_usvp_toy_v1__g1__beta_plus_4",
    ]
    assert [candidate.mutation_summary for candidate in batch.candidates] == [
        "operator[0].params.beta: 48 -> 44",
        "operator[0].params.beta: 48 -> 52",
    ]

    for candidate in batch.candidates:
        assert candidate.parent_attack_plan_id == plan.attack_plan_id
        assert candidate.generation == 1
        assert candidate.attack_plan.metadata.public is False
        assert candidate.attack_plan.metadata.created_by == "mutation_batch"
        assert candidate.attack_plan.claims.external_claim is False
        assert candidate.attack_plan.claims.estimated_time_bits is None
        assert "Not a security claim" in candidate.attack_plan.metadata.notes
        assert validate_attack_plan(candidate.attack_plan).valid is True


def test_candidate_mutation_batch_skips_schema_only_without_fake_candidates() -> None:
    plan = _plan("examples/attack_plans/lattice_ntru_schema_placeholder.json")

    batch = build_candidate_mutation_batch(
        [plan],
        run_id="unit-mutation",
        generation=1,
    )

    assert batch.summary == {
        "candidate_count": 0,
        "source_count": 1,
        "skipped_count": 1,
    }
    assert batch.candidates == []
    assert batch.skipped[0].attack_plan_id == "lattice_ntru_schema_placeholder_v1"
    assert batch.skipped[0].reason == "schema-only mutation skipped for NTRU"


def test_candidate_mutation_batch_generates_bkw_block_size_mutations() -> None:
    plan = _plan("examples/attack_plans/lattice_bkw_toy.json")

    batch = build_candidate_mutation_batch(
        [plan],
        run_id="unit-mutation",
        generation=3,
        max_mutations_per_plan=2,
    )

    assert [candidate.candidate_id for candidate in batch.candidates] == [
        "lattice_bkw_toy_v1__g3__block_size_minus_1",
        "lattice_bkw_toy_v1__g3__block_size_plus_1",
    ]
    assert [
        candidate.attack_plan.operators[0].params["block_size"]
        for candidate in batch.candidates
    ] == [
        7,
        9,
    ]
    assert [candidate.mutation_summary for candidate in batch.candidates] == [
        "operator[0].params.block_size: 8 -> 7",
        "operator[0].params.block_size: 8 -> 9",
    ]


def test_candidate_mutation_batch_generates_dual_hybrid_preprocessing() -> None:
    plan = _plan("examples/attack_plans/lattice_dual_hybrid_toy.json")

    batch = build_candidate_mutation_batch(
        [plan],
        run_id="unit-mutation",
        generation=4,
        max_mutations_per_plan=4,
    )

    assert [candidate.candidate_id for candidate in batch.candidates] == [
        "lattice_dual_hybrid_toy_v1__g4__operator_0_q_prime_div_2",
        "lattice_dual_hybrid_toy_v1__g4__operator_0_q_prime_times_2",
        "lattice_dual_hybrid_toy_v1__g4__operator_1_beta_minus_4",
        "lattice_dual_hybrid_toy_v1__g4__operator_1_beta_plus_4",
    ]
    assert batch.candidates[0].attack_plan.operators[0].params["q_prime"] == 64
    assert batch.candidates[1].attack_plan.operators[0].params["q_prime"] == 256
    assert batch.candidates[2].attack_plan.operators[1].params["beta"] == 56
    assert batch.candidates[3].attack_plan.operators[1].params["beta"] == 64
    for candidate in batch.candidates:
        assert validate_attack_plan(candidate.attack_plan).valid is True


def test_candidate_mutation_batch_generates_dual_hybrid_zeta_after_beta() -> None:
    plan = _plan("examples/attack_plans/lattice_dual_hybrid_toy.json")

    batch = build_candidate_mutation_batch(
        [plan],
        run_id="unit-mutation",
        generation=5,
        max_mutations_per_plan=6,
    )

    assert [candidate.candidate_id for candidate in batch.candidates][-2:] == [
        "lattice_dual_hybrid_toy_v1__g5__operator_1_zeta_minus_1",
        "lattice_dual_hybrid_toy_v1__g5__operator_1_zeta_plus_1",
    ]
    assert [
        candidate.attack_plan.operators[1].params["zeta"]
        for candidate in batch.candidates[-2:]
    ] == [
        7,
        9,
    ]


def test_candidate_mutation_batch_generates_code_based_lee_brickell_mutations() -> None:
    plan = _plan("examples/attack_plans/code_based_lee_brickell_toy.json")

    batch = build_candidate_mutation_batch(
        [plan],
        run_id="unit-code-based-mutation",
        generation=2,
        max_mutations_per_plan=4,
    )

    assert batch.summary == {
        "candidate_count": 1,
        "source_count": 1,
        "skipped_count": 0,
    }
    assert [candidate.candidate_id for candidate in batch.candidates] == [
        "code_based_lee_brickell_toy_v1__g2__p_plus_1"
    ]
    candidate = batch.candidates[0]
    assert candidate.mutation_summary == "operator[0].params.p: 1 -> 2"
    assert candidate.attack_plan.target.family.value == "CODE_BASED"
    assert candidate.attack_plan.metadata.public is False
    assert candidate.attack_plan.operators[0].params["p"] == 2
    assert validate_attack_plan(candidate.attack_plan).valid is True


def test_candidate_mutation_batch_generates_code_based_dumer_ell_mutations() -> None:
    plan = _plan("examples/attack_plans/code_based_dumer_toy.json")

    batch = build_candidate_mutation_batch(
        [plan],
        run_id="unit-code-based-mutation",
        generation=3,
        max_mutations_per_plan=4,
    )

    assert [candidate.candidate_id for candidate in batch.candidates] == [
        "code_based_dumer_toy_v1__g3__ell_minus_1",
        "code_based_dumer_toy_v1__g3__ell_plus_1",
    ]
    assert [
        candidate.attack_plan.operators[0].params["ell"]
        for candidate in batch.candidates
    ] == [1, 3]
    assert all(
        candidate.attack_plan.operators[0].params["p"] == 1
        for candidate in batch.candidates
    )
    assert all(
        validate_attack_plan(candidate.attack_plan).valid
        for candidate in batch.candidates
    )


def test_candidate_mutation_batch_generates_code_based_bjmm_rep_mutations() -> None:
    plan = _plan("examples/attack_plans/code_based_bjmm_toy.json")

    batch = build_candidate_mutation_batch(
        [plan],
        run_id="unit-code-based-mutation",
        generation=4,
        max_mutations_per_plan=6,
    )

    assert [candidate.candidate_id for candidate in batch.candidates] == [
        "code_based_bjmm_toy_v1__g4__ell_minus_1",
        "code_based_bjmm_toy_v1__g4__ell_plus_1",
        "code_based_bjmm_toy_v1__g4__representation_count_div_2",
        "code_based_bjmm_toy_v1__g4__representation_count_times_2",
    ]
    assert [
        candidate.attack_plan.operators[0].params["representation_count"]
        for candidate in batch.candidates[-2:]
    ] == [2, 8]
    assert [
        candidate.mutation_summary for candidate in batch.candidates[-2:]
    ] == [
        "operator[0].params.representation_count: 4 -> 2",
        "operator[0].params.representation_count: 4 -> 8",
    ]
    assert all(
        candidate.attack_plan.metadata.public is False
        for candidate in batch.candidates
    )
    assert all(
        validate_attack_plan(candidate.attack_plan).valid
        for candidate in batch.candidates
    )


def test_candidate_mutation_batch_generates_prange_target_mutations() -> None:
    plan = _plan("examples/attack_plans/code_based_prange_toy.json")

    batch = build_candidate_mutation_batch(
        [plan],
        run_id="unit-code-based-prange-target-mutation",
        generation=10,
        max_mutations_per_plan=4,
    )

    assert [candidate.candidate_id for candidate in batch.candidates] == [
        "code_based_prange_toy_v1__g10__target_w_minus_1",
        "code_based_prange_toy_v1__g10__target_w_plus_1",
    ]
    assert [candidate.mutation_summary for candidate in batch.candidates] == [
        (
            "target.w: 3 -> 2; "
            "target.claimed_security_bits: 32.0 -> None; "
            "target.name: toy_syndrome_31_16_w3 -> toy_syndrome_31_16_w2"
        ),
        (
            "target.w: 3 -> 4; "
            "target.claimed_security_bits: 32.0 -> None; "
            "target.name: toy_syndrome_31_16_w3 -> toy_syndrome_31_16_w4"
        ),
    ]
    assert [candidate.attack_plan.target.w for candidate in batch.candidates] == [
        2,
        4,
    ]
    assert [
        candidate.attack_plan.target.claimed_security_bits
        for candidate in batch.candidates
    ] == [None, None]
    assert [candidate.attack_plan.target.name for candidate in batch.candidates] == [
        "toy_syndrome_31_16_w2",
        "toy_syndrome_31_16_w4",
    ]
    assert all(
        candidate.attack_plan.target.family.value == "CODE_BASED"
        for candidate in batch.candidates
    )
    assert all(
        candidate.attack_plan.metadata.public is False
        for candidate in batch.candidates
    )
    assert all(
        validate_attack_plan(candidate.attack_plan).valid
        for candidate in batch.candidates
    )


def test_candidate_mutation_batch_skips_code_based_prange_fixture_targets() -> None:
    plan = _plan("examples/attack_plans/code_based_prange_toy_n15.json")

    batch = build_candidate_mutation_batch(
        [plan],
        run_id="unit-code-based-prange-target-mutation",
        generation=10,
        max_mutations_per_plan=4,
    )

    assert batch.summary == {
        "candidate_count": 0,
        "source_count": 1,
        "skipped_count": 1,
    }
    assert batch.candidates == []
    assert batch.skipped[0].attack_plan_id == "code_based_prange_toy_n15_v1"
    assert batch.skipped[0].reason == "fixture-bound mutation skipped for CODE_BASED"


def test_candidate_mutation_batch_fixture_bound_skip_precedes_operator_rules() -> None:
    plan = _plan("examples/attack_plans/code_based_lee_brickell_toy.json")
    fixture_bound_plan = plan.model_copy(
        update={
            "attack_plan_id": "code_based_lee_brickell_fixture_bound_v1",
            "constraints": plan.constraints.model_copy(
                update={
                    "require_reproducibility_on_downscaled_instances": True,
                    "downscaled_reproduction_fixture": (
                        "benchmarks/code_based_toy_isd/fixtures/"
                        "toy_syndrome_15_7_w2_fixture.json"
                    ),
                }
            ),
        },
        deep=True,
    )

    batch = build_candidate_mutation_batch(
        [fixture_bound_plan],
        run_id="unit-fixture-bound-mutation",
        generation=1,
        max_mutations_per_plan=4,
    )

    assert batch.summary == {
        "candidate_count": 0,
        "source_count": 1,
        "skipped_count": 1,
    }
    assert batch.candidates == []
    assert batch.skipped[0].attack_plan_id == (
        "code_based_lee_brickell_fixture_bound_v1"
    )
    assert batch.skipped[0].reason == "fixture-bound mutation skipped for CODE_BASED"


def test_candidate_mutation_batch_generates_multivariate_hybrid_mutations() -> None:
    plan = _plan("examples/attack_plans/multivariate_mq_hybrid_toy.json")

    batch = build_candidate_mutation_batch(
        [plan],
        run_id="unit-multivariate-mutation",
        generation=5,
        max_mutations_per_plan=4,
    )

    assert [candidate.candidate_id for candidate in batch.candidates] == [
        "multivariate_mq_hybrid_toy_v1__g5__guessed_variables_minus_1",
        "multivariate_mq_hybrid_toy_v1__g5__guessed_variables_plus_1",
    ]
    assert [
        candidate.attack_plan.operators[0].params["guessed_variables"]
        for candidate in batch.candidates
    ] == [2, 4]
    assert all(
        candidate.attack_plan.target.family.value == "MULTIVARIATE"
        for candidate in batch.candidates
    )
    assert all(
        validate_attack_plan(candidate.attack_plan).valid
        for candidate in batch.candidates
    )


def test_candidate_mutation_batch_generates_multivariate_mq_target_mutations() -> None:
    plan = _plan("examples/attack_plans/multivariate_mq_toy.json")

    batch = build_candidate_mutation_batch(
        [plan],
        run_id="unit-multivariate-mq-target-mutation",
        generation=11,
        max_mutations_per_plan=4,
    )

    assert [candidate.candidate_id for candidate in batch.candidates] == [
        "multivariate_mq_toy_v1__g11__target_variables_minus_1",
        "multivariate_mq_toy_v1__g11__target_variables_plus_1",
        "multivariate_mq_toy_v1__g11__target_equations_minus_1",
        "multivariate_mq_toy_v1__g11__target_equations_plus_1",
    ]
    assert [candidate.mutation_summary for candidate in batch.candidates] == [
        (
            "target.variables: 8 -> 7; "
            "target.claimed_security_bits: 32.0 -> None; "
            "target.name: toy_mq_gf16_v8_e6 -> toy_mq_gf16_v7_e6"
        ),
        (
            "target.variables: 8 -> 9; "
            "target.claimed_security_bits: 32.0 -> None; "
            "target.name: toy_mq_gf16_v8_e6 -> toy_mq_gf16_v9_e6"
        ),
        (
            "target.equations: 6 -> 5; "
            "target.claimed_security_bits: 32.0 -> None; "
            "target.name: toy_mq_gf16_v8_e6 -> toy_mq_gf16_v8_e5"
        ),
        (
            "target.equations: 6 -> 7; "
            "target.claimed_security_bits: 32.0 -> None; "
            "target.name: toy_mq_gf16_v8_e6 -> toy_mq_gf16_v8_e7"
        ),
    ]
    assert [
        (candidate.attack_plan.target.variables, candidate.attack_plan.target.equations)
        for candidate in batch.candidates
    ] == [
        (7, 6),
        (9, 6),
        (8, 5),
        (8, 7),
    ]
    assert [
        candidate.attack_plan.target.claimed_security_bits
        for candidate in batch.candidates
    ] == [None, None, None, None]
    assert [candidate.attack_plan.target.name for candidate in batch.candidates] == [
        "toy_mq_gf16_v7_e6",
        "toy_mq_gf16_v9_e6",
        "toy_mq_gf16_v8_e5",
        "toy_mq_gf16_v8_e7",
    ]
    assert all(
        candidate.attack_plan.target.family.value == "MULTIVARIATE"
        for candidate in batch.candidates
    )
    assert all(
        candidate.attack_plan.metadata.public is False
        for candidate in batch.candidates
    )
    assert all(
        validate_attack_plan(candidate.attack_plan).valid
        for candidate in batch.candidates
    )


def test_candidate_mutation_batch_skips_multivariate_mq_fixture_targets() -> None:
    plan = _plan("examples/attack_plans/multivariate_mq_hybrid_gf2_toy.json")

    batch = build_candidate_mutation_batch(
        [plan],
        run_id="unit-multivariate-mq-target-mutation",
        generation=11,
        max_mutations_per_plan=4,
    )

    assert batch.summary == {
        "candidate_count": 0,
        "source_count": 1,
        "skipped_count": 1,
    }
    assert batch.candidates == []
    assert batch.skipped[0].attack_plan_id == "multivariate_mq_hybrid_gf2_toy_v1"
    assert batch.skipped[0].reason == (
        "fixture-bound mutation skipped for MULTIVARIATE"
    )


def test_candidate_mutation_batch_mutates_multivariate_degree_bound() -> None:
    plan = _plan("examples/attack_plans/multivariate_mq_degree_bound_toy.json")

    batch = build_candidate_mutation_batch(
        [plan],
        run_id="unit-multivariate-mutation",
        generation=6,
        max_mutations_per_plan=4,
    )

    assert [candidate.candidate_id for candidate in batch.candidates] == [
        "multivariate_mq_degree_bound_toy_v1__g6__degree_bound_minus_1",
        "multivariate_mq_degree_bound_toy_v1__g6__degree_bound_plus_1",
    ]
    assert [
        candidate.attack_plan.operators[0].params["degree_bound"]
        for candidate in batch.candidates
    ] == [2, 4]
    assert all(
        candidate.attack_plan.metadata.public is False
        for candidate in batch.candidates
    )
    assert all(
        validate_attack_plan(candidate.attack_plan).valid
        for candidate in batch.candidates
    )


def test_candidate_mutation_batch_generates_hash_preimage_digest_mutations() -> None:
    plan = _plan("examples/attack_plans/hash_based_preimage_toy.json")

    batch = build_candidate_mutation_batch(
        [plan],
        run_id="unit-hash-based-mutation",
        generation=7,
        max_mutations_per_plan=4,
    )

    assert [candidate.candidate_id for candidate in batch.candidates] == [
        "hash_based_preimage_toy_v1__g7__target_n_minus_8",
        "hash_based_preimage_toy_v1__g7__target_n_plus_8",
    ]
    assert [candidate.mutation_summary for candidate in batch.candidates] == [
        (
            "target.n: 32 -> 24; "
            "target.claimed_security_bits: 32.0 -> 24.0; "
            "target.name: toy_hash_preimage_32 -> toy_hash_preimage_24"
        ),
        (
            "target.n: 32 -> 40; "
            "target.claimed_security_bits: 32.0 -> 40.0; "
            "target.name: toy_hash_preimage_32 -> toy_hash_preimage_40"
        ),
    ]
    assert [candidate.attack_plan.target.n for candidate in batch.candidates] == [
        24,
        40,
    ]
    assert [
        candidate.attack_plan.target.claimed_security_bits
        for candidate in batch.candidates
    ] == [24.0, 40.0]
    assert [candidate.attack_plan.target.name for candidate in batch.candidates] == [
        "toy_hash_preimage_24",
        "toy_hash_preimage_40",
    ]
    assert all(
        candidate.attack_plan.target.family.value == "HASH_BASED"
        for candidate in batch.candidates
    )
    assert all(
        candidate.attack_plan.metadata.public is False
        for candidate in batch.candidates
    )
    assert all(
        validate_attack_plan(candidate.attack_plan).valid
        for candidate in batch.candidates
    )


def test_candidate_mutation_batch_skips_hash_fixture_bound_targets() -> None:
    plan = _plan("examples/attack_plans/hash_based_collision_toy.json")

    batch = build_candidate_mutation_batch(
        [plan],
        run_id="unit-hash-based-mutation",
        generation=7,
        max_mutations_per_plan=4,
    )

    assert batch.summary == {
        "candidate_count": 0,
        "source_count": 1,
        "skipped_count": 1,
    }
    assert batch.candidates == []
    assert batch.skipped[0].attack_plan_id == "hash_based_collision_toy_v1"
    assert batch.skipped[0].reason == "fixture-bound mutation skipped for HASH_BASED"


def test_candidate_mutation_batch_generates_implementation_kat_mutations() -> None:
    plan = _plan("examples/attack_plans/implementation_security_kat_toy.json")

    batch = build_candidate_mutation_batch(
        [plan],
        run_id="unit-implementation-security-mutation",
        generation=8,
        max_mutations_per_plan=4,
    )

    assert [candidate.candidate_id for candidate in batch.candidates] == [
        "implementation_security_kat_toy_v1__g8__vector_count_minus_1",
        "implementation_security_kat_toy_v1__g8__vector_count_plus_1",
    ]
    assert [candidate.mutation_summary for candidate in batch.candidates] == [
        "operator[0].params.vector_count: 2 -> 1",
        "operator[0].params.vector_count: 2 -> 3",
    ]
    assert [
        candidate.attack_plan.operators[0].params["vector_count"]
        for candidate in batch.candidates
    ] == [1, 3]
    assert all(
        candidate.attack_plan.target.family.value == "IMPLEMENTATION_SECURITY"
        for candidate in batch.candidates
    )
    assert all(
        candidate.attack_plan.metadata.public is False
        for candidate in batch.candidates
    )
    assert all(
        validate_attack_plan(candidate.attack_plan).valid
        for candidate in batch.candidates
    )


def test_candidate_mutation_batch_skips_implementation_fixture_bound_targets() -> None:
    plan = _plan("examples/attack_plans/implementation_security_mldsa_kat_toy.json")

    batch = build_candidate_mutation_batch(
        [plan],
        run_id="unit-implementation-security-mutation",
        generation=8,
        max_mutations_per_plan=4,
    )

    assert batch.summary == {
        "candidate_count": 0,
        "source_count": 1,
        "skipped_count": 1,
    }
    assert batch.candidates == []
    assert batch.skipped[0].attack_plan_id == (
        "implementation_security_mldsa_kat_toy_v1"
    )
    assert batch.skipped[0].reason == (
        "fixture-bound mutation skipped for IMPLEMENTATION_SECURITY"
    )


def test_candidate_mutation_batch_generates_isogeny_historical_mutations() -> None:
    plan = _plan("examples/attack_plans/isogeny_historical_toy.json")

    batch = build_candidate_mutation_batch(
        [plan],
        run_id="unit-isogeny-historical-mutation",
        generation=9,
        max_mutations_per_plan=4,
    )

    assert [candidate.candidate_id for candidate in batch.candidates] == [
        "isogeny_historical_toy_path_v1__g9__walk_length_minus_1",
        "isogeny_historical_toy_path_v1__g9__walk_length_plus_1",
        "isogeny_historical_toy_path_v1__g9__branching_factor_minus_1",
        "isogeny_historical_toy_path_v1__g9__branching_factor_plus_1",
    ]
    assert [candidate.mutation_summary for candidate in batch.candidates] == [
        "operator[0].params.walk_length: 8 -> 7",
        "operator[0].params.walk_length: 8 -> 9",
        "operator[0].params.branching_factor: 4 -> 3",
        "operator[0].params.branching_factor: 4 -> 5",
    ]
    assert [
        candidate.attack_plan.operators[0].params["walk_length"]
        for candidate in batch.candidates[:2]
    ] == [7, 9]
    assert [
        candidate.attack_plan.operators[0].params["branching_factor"]
        for candidate in batch.candidates[2:]
    ] == [3, 5]
    assert all(
        candidate.attack_plan.target.family.value == "ISOGENY_HISTORICAL"
        for candidate in batch.candidates
    )
    assert all(
        candidate.attack_plan.metadata.public is False
        for candidate in batch.candidates
    )
    assert all(
        validate_attack_plan(candidate.attack_plan).valid
        for candidate in batch.candidates
    )


def test_candidate_mutation_batch_skips_isogeny_fixture_bound_targets() -> None:
    plan = _plan("examples/attack_plans/isogeny_historical_commutative_walk_toy.json")

    batch = build_candidate_mutation_batch(
        [plan],
        run_id="unit-isogeny-historical-mutation",
        generation=9,
        max_mutations_per_plan=4,
    )

    assert batch.summary == {
        "candidate_count": 0,
        "source_count": 1,
        "skipped_count": 1,
    }
    assert batch.candidates == []
    assert batch.skipped[0].attack_plan_id == (
        "isogeny_historical_commutative_walk_toy_v1"
    )
    assert batch.skipped[0].reason == (
        "fixture-bound mutation skipped for ISOGENY_HISTORICAL"
    )


def test_write_candidate_mutation_batch_separates_manifest_from_plan_directory(
    tmp_path: Path,
) -> None:
    plan = _plan("examples/attack_plans/lattice_primal_usvp_toy.json")

    batch = write_candidate_mutation_batch(
        [plan],
        tmp_path,
        run_id="unit-mutation",
        generation=2,
        max_mutations_per_plan=1,
    )

    manifest = json.loads((tmp_path / "mutation_manifest.json").read_text())
    plan_files = sorted((tmp_path / "plans").glob("*.json"))

    assert manifest["schema_version"] == CANDIDATE_MUTATION_BATCH_SCHEMA
    assert manifest["summary"]["candidate_count"] == 1
    assert manifest["candidates"][0]["path"] == (
        "plans/lattice_primal_usvp_toy_v1__g2__beta_minus_4.json"
    )
    assert len(plan_files) == 1
    mutated_plan = AttackPlan.model_validate_json(plan_files[0].read_text())
    assert mutated_plan.attack_plan_id == (
        "lattice_primal_usvp_toy_v1__g2__beta_minus_4"
    )
    assert mutated_plan.operators[0].params["beta"] == 44
    assert batch.candidates[0].attack_plan == mutated_plan


def test_build_archive_candidate_mutation_batch_links_elite_parent_metadata() -> None:
    plan = _plan("examples/attack_plans/lattice_primal_usvp_toy.json")
    source_record = _record(
        plan=plan,
        candidate_id="elite-candidate",
        trace_id="elite-trace",
        generation=2,
        score=-90.0,
        accepted=True,
    )
    archive = build_evolution_archive([source_record], run_id="training")

    batch = build_archive_candidate_mutation_batch(
        archive,
        [source_record],
        run_id="archive-mutations",
        max_mutations_per_elite=2,
    )

    assert batch.summary == {
        "candidate_count": 2,
        "source_count": 1,
        "skipped_count": 0,
    }
    assert [candidate.parent_candidate_id for candidate in batch.candidates] == [
        "elite-candidate",
        "elite-candidate",
    ]
    assert [candidate.parent_trace_id for candidate in batch.candidates] == [
        "elite-trace",
        "elite-trace",
    ]
    assert [candidate.generation for candidate in batch.candidates] == [3, 3]
    assert [candidate.candidate_id for candidate in batch.candidates] == [
        "lattice_primal_usvp_toy_v1__g3__beta_minus_4",
        "lattice_primal_usvp_toy_v1__g3__beta_plus_4",
    ]
    assert all(
        "Not a security claim" in candidate.attack_plan.metadata.notes
        for candidate in batch.candidates
    )


def test_build_archive_candidate_mutation_batch_rejects_missing_source_trace() -> None:
    plan = _plan("examples/attack_plans/lattice_primal_usvp_toy.json")
    source_record = _record(
        plan=plan,
        candidate_id="elite-candidate",
        trace_id="elite-trace",
        generation=0,
        score=-90.0,
        accepted=True,
    )
    archive = build_evolution_archive([source_record], run_id="training")

    try:
        build_archive_candidate_mutation_batch(
            archive,
            [],
            run_id="archive-mutations",
        )
    except ValueError as exc:
        assert "missing from source trace" in str(exc)
    else:
        raise AssertionError("missing source trace was accepted")


def test_write_archive_candidate_mutation_batch_records_parent_trace_links(
    tmp_path: Path,
) -> None:
    plan = _plan("examples/attack_plans/lattice_primal_usvp_toy.json")
    source_record = _record(
        plan=plan,
        candidate_id="elite-candidate",
        trace_id="elite-trace",
        generation=1,
        score=-90.0,
        accepted=True,
    )
    archive = build_evolution_archive([source_record], run_id="training")

    batch = write_archive_candidate_mutation_batch(
        archive,
        [source_record],
        tmp_path,
        run_id="archive-mutations",
        max_mutations_per_elite=1,
    )

    manifest = json.loads((tmp_path / "mutation_manifest.json").read_text())
    plan_files = sorted((tmp_path / "plans").glob("*.json"))

    assert batch.summary == {
        "candidate_count": 1,
        "source_count": 1,
        "skipped_count": 0,
    }
    assert manifest["candidates"][0]["parent_candidate_id"] == "elite-candidate"
    assert manifest["candidates"][0]["parent_trace_id"] == "elite-trace"
    assert manifest["candidates"][0]["generation"] == 2
    assert len(plan_files) == 1
    mutated_plan = AttackPlan.model_validate_json(plan_files[0].read_text())
    assert mutated_plan.metadata.public is False
    assert batch.candidates[0].attack_plan == mutated_plan


def _plan(path: str) -> AttackPlan:
    return AttackPlan.model_validate_json(Path(path).read_text())


def _record(
    *,
    plan: AttackPlan,
    candidate_id: str,
    trace_id: str,
    generation: int,
    score: float,
    accepted: bool,
) -> TraceRecord:
    record = TraceRecord.from_evaluation(
        run_id="training",
        candidate_id=candidate_id,
        parent_id=None,
        generation=generation,
        mutation_summary="unit test",
        attack_plan=plan,
        evaluation={
            "combined_score": score,
            "evaluation_status": "ok" if accepted else "invalid",
            "feature_family": plan.target.family.value,
            "feature_attack_type": "primal_usvp",
            "feature_memory_bucket": "low",
            "feature_assumption_bucket": "some",
            "feature_estimator_model": "mock-lattice-estimator",
            "valid": accepted,
        },
        accepted=accepted,
        public_release_ok=accepted,
        redaction_reason=None if accepted else "invalid",
    )
    return record.model_copy(update={"trace_id": trace_id})
