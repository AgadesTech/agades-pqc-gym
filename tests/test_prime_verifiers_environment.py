from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from types import ModuleType

import pytest

SOURCE_DOCS = Path("docs")
SOURCE_LEAN = Path("formal/lean")
ENV_MODULE = Path(
    "prime_intellect/verifiers_environment/agades_pqc_verifier_env.py"
)
PACKAGED_DOCS = Path("prime_intellect/verifiers_environment/docs")
PACKAGED_LEAN = Path("prime_intellect/verifiers_environment/formal/lean")
LATTICE_PLAN = Path(
    "prime_intellect/verifiers_environment/data/lattice_primal_usvp_toy.json"
)


def test_prime_verifiers_environment_exposes_term_level_reward_report() -> None:
    module = _load_environment_module()
    raw_plan = LATTICE_PLAN.read_text(encoding="utf-8")
    task_info = _task_info_for(module, "lattice_primal_usvp_toy_v1")

    report = module.score_attack_plan_completion_report(
        _assistant_completion(raw_plan),
        info=task_info,
        require_info=True,
    )

    assert report["schema_version"] == "agades.pqc.prime.reward_report.v1"
    assert report["aggregate_reward"] == 1.0
    assert report["accepted"] is True
    assert report["single_json_object"] is True
    assert report["reward_profile"] == "strict"
    assert report["rubric_scores"] == {
        "accepted_attack_plan": 1.0,
        "single_json_object": 1.0,
        "formal_validity": 1.0,
        "cryptographic_applicability": 1.0,
        "no_security_overclaim": 1.0,
        "student_readability": 1.0,
        "reproducibility": 1.0,
        "reviewer_quality": 1.0,
        "task_match": 1.0,
        "proof_obligation_coverage": 1.0,
    }
    assert report["formal_summary"]["typed_proof_obligations"] == report[
        "formal_summary"
    ]["proof_obligations"]
    formal_binding = report["formal_artifact_binding"]
    assert formal_binding["schema_version"] == (
        "agades.pqc.rl.formal_artifact_binding.v1"
    )
    assert formal_binding["attack_plan_id"] == "lattice_primal_usvp_toy_v1"
    assert formal_binding["status"] == "attached"
    assert formal_binding["review_governance_ok"] is True
    assert formal_binding["review_governance"]["schema_version"] == (
        "agades.pqc.formal.proof_artifact.reviewer_governance_binding.v1"
    )
    assert report["review_governance_ok"] is True


def test_prime_verifiers_environment_blocks_prefixed_json_in_term_report() -> None:
    module = _load_environment_module()
    raw_plan = LATTICE_PLAN.read_text(encoding="utf-8")

    report = module.score_attack_plan_completion_report(
        _assistant_completion(f"candidate:\n{raw_plan}"),
        info=_task_info_for(module, "lattice_primal_usvp_toy_v1"),
        require_info=True,
    )

    assert report["aggregate_reward"] == 0.0
    assert report["accepted"] is False
    assert report["single_json_object"] is False
    assert report["blocking_reasons"] == ["single_json_object"]
    assert set(report["rubric_scores"]) == set(module.PRIME_RUBRIC_TERMS)
    assert all(score == 0.0 for score in report["rubric_scores"].values())


def test_prime_verifiers_environment_accepts_explicit_project_root() -> None:
    module = _load_environment_module()
    raw_plan = LATTICE_PLAN.read_text(encoding="utf-8")

    report = module.score_attack_plan_completion_report(
        _assistant_completion(raw_plan),
        info=_task_info_for(module, "lattice_primal_usvp_toy_v1"),
        require_info=True,
        project_root=Path.cwd(),
    )

    assert report["aggregate_reward"] == 1.0
    assert report["formal_artifact_binding"]["status"] == "attached"


def test_prime_verifiers_environment_uses_packaged_formal_artifacts() -> None:
    module = _load_environment_module()
    raw_plan = LATTICE_PLAN.read_text(encoding="utf-8")

    assert module._project_root(None) == module.PACKAGE_DIR

    report = module.score_attack_plan_completion_report(
        _assistant_completion(raw_plan),
        info=_task_info_for(module, "lattice_primal_usvp_toy_v1"),
        require_info=True,
    )

    assert report["aggregate_reward"] == 1.0
    assert report["formal_artifact_binding"]["status"] == "attached"


def test_prime_verifiers_environment_packaged_artifacts_match_source() -> None:
    assert _file_digests(PACKAGED_DOCS, suffix=".json") == _file_digests(
        SOURCE_DOCS,
        suffix=".json",
    )
    assert _file_digests(PACKAGED_LEAN) == _file_digests(
        SOURCE_LEAN,
        ignored_parts=frozenset({".lake"}),
    )


def test_prime_verifiers_environment_rejects_bad_project_root(tmp_path: Path) -> None:
    module = _load_environment_module()
    raw_plan = LATTICE_PLAN.read_text(encoding="utf-8")

    try:
        module.score_attack_plan_completion_report(
            _assistant_completion(raw_plan),
            info=_task_info_for(module, "lattice_primal_usvp_toy_v1"),
            require_info=True,
            project_root=tmp_path,
        )
    except ValueError as exc:
        assert "required Agades formal artifacts" in str(exc)
    else:
        raise AssertionError("bad project_root should be rejected")


def test_prime_verifiers_environment_builds_named_rubric_functions() -> None:
    module = _load_environment_module()

    functions = module.build_rubric_functions()

    assert [func.__name__ for func in functions] == list(module.PRIME_RUBRIC_TERMS)


def test_prime_verifiers_environment_weights_only_primary_reward() -> None:
    module = _load_environment_module()

    assert module.build_rubric_weights() == [
        1.0,
        0.0,
        *[0.0 for _ in module.REWARD_TERMS],
    ]


def test_prime_verifiers_environment_dense_profile_is_training_only_signal() -> None:
    module = _load_environment_module()
    invalid_json_object = '{"not": "an attack plan"}'
    task_info = _task_info_for(module, "lattice_primal_usvp_toy_v1")

    strict_report = module.score_attack_plan_completion_report(
        _assistant_completion(invalid_json_object),
        info=task_info,
        reward_profile="strict",
    )
    dense_report = module.score_attack_plan_completion_report(
        _assistant_completion(invalid_json_object),
        info=task_info,
        reward_profile="pedagogical_dense",
    )

    assert strict_report["aggregate_reward"] == 0.0
    assert strict_report["accepted"] is False
    assert dense_report["aggregate_reward"] == 0.10
    assert dense_report["accepted"] is False
    assert dense_report["single_json_object"] is True
    assert dense_report["rubric_scores"]["single_json_object"] == 1.0
    assert sum(module.build_rubric_weights("pedagogical_dense")) == 1.0
    assert module.build_rubric_weights("pedagogical_dense") == [
        0.30,
        0.10,
        0.15,
        0.10,
        0.10,
        0.07,
        0.05,
        0.05,
        0.04,
        0.04,
    ]


def test_prime_verifiers_environment_grades_format_repair_wrapped_json() -> None:
    module = _load_environment_module()
    raw_plan = LATTICE_PLAN.read_text(encoding="utf-8")
    wrapped_plan = f"Here is the plan:\n```json\n{raw_plan}\n```"
    task_info = _task_info_for(module, "lattice_primal_usvp_toy_v1")

    strict_report = module.score_attack_plan_completion_report(
        _assistant_completion(wrapped_plan),
        info=task_info,
        reward_profile="strict",
    )
    repair_report = module.score_attack_plan_completion_report(
        _assistant_completion(wrapped_plan),
        info=task_info,
        reward_profile="format_repair_dense",
    )
    exact_report = module.score_attack_plan_completion_report(
        _assistant_completion(raw_plan),
        info=task_info,
        reward_profile="format_repair_dense",
    )

    assert strict_report["aggregate_reward"] == 0.0
    assert repair_report["accepted"] is False
    assert repair_report["single_json_object"] is False
    assert 0.0 < repair_report["aggregate_reward"] < exact_report["aggregate_reward"]
    assert "wrapped_or_prefixed_json" in repair_report["blocking_reasons"]
    assert repair_report["rubric_scores"]["accepted_attack_plan"] == 0.5
    assert repair_report["rubric_scores"]["formal_validity"] == 1.0
    assert exact_report["aggregate_reward"] == 1.0
    assert sum(module.build_rubric_weights("format_repair_dense")) == 1.0
    assert module.build_rubric_weights("format_repair_dense") == [
        0.22,
        0.16,
        0.20,
        0.04,
        0.15,
        0.15,
        0.02,
        0.02,
        0.03,
        0.01,
    ]


def test_prime_verifier_quarantines_hidden_reasoning_from_readability() -> None:
    module = _load_environment_module()
    raw_plan = LATTICE_PLAN.read_text(encoding="utf-8")
    task_info = _task_info_for(module, "lattice_primal_usvp_toy_v1")

    concise_report = module.score_attack_plan_completion_report(
        [{"role": "assistant", "content": raw_plan}],
        info=task_info,
        reward_profile="format_repair_dense",
    )
    verbose_report = module.score_attack_plan_completion_report(
        [
            {
                "role": "assistant",
                "content": raw_plan,
                "reasoning_content": "x" * 10_000,
            }
        ],
        info=task_info,
        reward_profile="format_repair_dense",
    )

    assert concise_report["accepted"] is True
    assert verbose_report["accepted"] is True
    assert concise_report["rubric_scores"]["student_readability"] == 1.0
    assert verbose_report["rubric_scores"]["student_readability"] == 1.0
    assert verbose_report["aggregate_reward"] == concise_report["aggregate_reward"]


def test_prime_verifiers_environment_penalizes_visible_wrapper_text() -> None:
    module = _load_environment_module()
    raw_plan = LATTICE_PLAN.read_text(encoding="utf-8")
    task_info = _task_info_for(module, "lattice_primal_usvp_toy_v1")

    report = module.score_attack_plan_completion_report(
        [{"role": "assistant", "content": f"```json\n{raw_plan}\n```"}],
        info=task_info,
        reward_profile="format_repair_dense",
    )

    assert report["accepted"] is False
    assert report["single_json_object"] is False
    assert report["rubric_scores"]["student_readability"] == 0.5
    assert "wrapped_or_prefixed_json" in report["blocking_reasons"]


def test_prime_verifiers_environment_decoy_output_is_not_accepted() -> None:
    module = _load_environment_module()
    task_info = _task_info_for(module, "lattice_primal_usvp_toy_v1")
    decoy = Path(
        "prime_intellect/verifiers_environment/data/code_based_prange_toy.json"
    ).read_text(encoding="utf-8")

    report = module.score_attack_plan_completion_report(
        _assistant_completion(decoy),
        info=task_info,
        reward_profile="format_repair_dense",
    )

    assert report["accepted"] is False
    assert report["single_json_object"] is True
    assert report["rubric_scores"]["single_json_object"] == 1.0
    assert report["rubric_scores"]["accepted_attack_plan"] == 0.0
    assert report["rubric_scores"]["formal_validity"] == 0.0
    assert report["rubric_scores"]["cryptographic_applicability"] == 0.0
    assert report["rubric_scores"]["no_security_overclaim"] == 0.0
    assert report["rubric_scores"]["task_match"] == 0.0
    assert "task_match" in report["blocking_reasons"]
    assert report["aggregate_reward"] <= 0.25


def test_prime_verifiers_environment_scores_embedded_target_match_over_decoy() -> None:
    module = _load_environment_module()
    row = module.build_dataset_rows(
        attack_plan_id="lattice_bdd_toy_v1",
        challenge_suite=True,
        challenge_type="wrong_family_decoy_repair",
    )[0]
    raw_plan = module._raw_json_for_task_info(row["info"]["task_metadata"])
    broken_output = module._claims_guard_decoy_wrapped_invalid_output(raw_plan)

    report = module.score_attack_plan_completion_report(
        _assistant_completion(broken_output),
        info=row["info"],
        require_info=True,
        reward_profile="format_repair_dense",
    )

    assert report["accepted"] is False
    assert report["single_json_object"] is False
    assert report["rubric_scores"]["formal_validity"] == 0.0
    assert report["rubric_scores"]["no_security_overclaim"] == 0.0
    assert "no_security_overclaim" in report["blocking_reasons"]
    assert report["aggregate_reward"] < 0.455


def test_prime_wrong_family_decoy_prompt_makes_claim_repair_explicit() -> None:
    module = _load_environment_module()
    row = module.build_dataset_rows(
        attack_plan_id="lattice_bdd_toy_v1",
        challenge_suite=True,
        challenge_type="wrong_family_decoy_repair",
    )[0]

    prompt = row["prompt"][0]["content"]

    assert "Ignore Candidate object 1 completely." in prompt
    assert "repaired Candidate object 2 AttackPlan" in prompt
    assert "estimated_time_bits=null" in prompt
    assert "estimated_memory_bits=null" in prompt
    assert "success_probability=null" in prompt
    assert "Do not add external_claim or source." in prompt
    assert "Keep the answer compact" in prompt
    assert "do not add new explanatory notes" in prompt


def test_prime_verifiers_environment_rejects_pre_evaluation_claim_estimates() -> None:
    module = _load_environment_module()
    raw_plan = LATTICE_PLAN.read_text(encoding="utf-8")
    broken_plan = module._claims_guard_invalid_output(raw_plan)
    task_info = _task_info_for(module, "lattice_primal_usvp_toy_v1")

    broken_report = module.score_attack_plan_completion_report(
        _assistant_completion(broken_plan),
        info=task_info,
        require_info=True,
        reward_profile="format_repair_dense",
    )
    repaired_report = module.score_attack_plan_completion_report(
        _assistant_completion(raw_plan),
        info=task_info,
        require_info=True,
        reward_profile="format_repair_dense",
    )

    assert broken_report["accepted"] is False
    assert broken_report["single_json_object"] is True
    assert broken_report["rubric_scores"]["single_json_object"] == 1.0
    assert broken_report["rubric_scores"]["formal_validity"] == 0.0
    assert "schema_valid" in broken_report["blocking_reasons"]
    assert repaired_report["accepted"] is True
    assert repaired_report["aggregate_reward"] == 1.0


def test_prime_verifiers_environment_format_rubric_uses_profile() -> None:
    module = _load_environment_module()
    raw_plan = LATTICE_PLAN.read_text(encoding="utf-8")
    wrapped_completion = _assistant_completion(
        f"Here is the plan:\n```json\n{raw_plan}\n```"
    )
    task_info = _task_info_for(module, "lattice_primal_usvp_toy_v1")

    strict_formal_score = module._rubric_score(
        wrapped_completion,
        "formal_validity",
        info=task_info,
        project_root=None,
    )
    repair_formal_score = module._rubric_score(
        wrapped_completion,
        "formal_validity",
        info=task_info,
        project_root=None,
        reward_profile="format_repair_dense",
    )

    assert strict_formal_score == 0.0
    assert repair_formal_score == 1.0


def test_prime_verifiers_environment_filters_dataset_rows() -> None:
    module = _load_environment_module()

    rows = module.build_dataset_rows(
        attack_plan_id="lattice_primal_usvp_toy_v1"
    )

    assert len(rows) == 1
    assert rows[0]["info"]["target_family"] == "LWE"
    assert module.build_dataset_rows(target_family="LWE")

    accepted_lwe_rows = module.build_dataset_rows(
        target_family="LWE",
        seed_accepted=True,
    )
    unsupported_lwe_rows = module.build_dataset_rows(
        target_family="LWE",
        seed_accepted=False,
    )

    assert accepted_lwe_rows
    assert unsupported_lwe_rows
    assert all(row["info"]["seed_accepted"] is True for row in accepted_lwe_rows)
    assert all(row["info"]["target_family"] == "LWE" for row in accepted_lwe_rows)
    assert all(row["info"]["seed_accepted"] is False for row in unsupported_lwe_rows)
    assert {
        row["info"]["attack_plan_id"]
        for row in unsupported_lwe_rows
    } >= {"lattice_lwe_modulus_switching_primary_v1"}


def test_prime_verifiers_environment_builds_discriminating_challenge_rows() -> None:
    module = _load_environment_module()

    rows = module.build_dataset_rows(
        attack_plan_id="lattice_bdd_toy_v1",
        challenge_suite=True,
    )

    assert [row["info"]["challenge_type"] for row in rows] == [
        "claims_guard_repair",
        "semantic_mutation_repair",
        "wrong_family_decoy_repair",
        "operator_mismatch_repair",
        "missing_hypothesis_repair",
        "invented_complexity_repair",
    ]
    for row in rows:
        info = row["info"]
        prompt = row["prompt"][0]["content"]
        task_metadata = info["task_metadata"]
        assert info["schema_version"] == "agades.pqc.prime.challenge_info.v1"
        assert info["expected_behavior"] in {
            "mutate_attackplan",
            "repair_attackplan",
        }
        assert info["private_data_allowed"] is False
        assert info["security_claims_allowed"] is False
        assert info["heldout_split"] in {"train", "heldout"}
        assert row["answer"] in {"repair_attackplan", "mutate_attackplan"}
        assert task_metadata["attack_plan_id"] == "lattice_bdd_toy_v1"
        assert "Return" in prompt
        assert "Toy/demo verifier output only" in prompt


def test_prime_verifiers_environment_builds_unsupported_refusal_rows() -> None:
    module = _load_environment_module()

    rows = module.build_dataset_rows(
        attack_plan_id="lattice_lwe_modulus_switching_primary_v1",
        challenge_suite=True,
        challenge_type="unsupported_refusal",
    )

    assert len(rows) == 1
    row = rows[0]
    info = row["info"]
    prompt = row["prompt"][0]["content"]
    task_metadata = info["task_metadata"]
    assert row["answer"] == "refuse_unsupported"
    assert info["challenge_type"] == "unsupported_refusal"
    assert info["expected_behavior"] == "refuse_unsupported"
    assert task_metadata["seed_accepted"] is False
    assert task_metadata["seed_evaluation_status"] == "unsupported"
    assert "Do not repair it into a fake working AttackPlan" in prompt
    assert '"unsupported_refusal"' in prompt
    assert 'reason="unsupported_or_schema_only"' in prompt
    assert "Do not include attack_plan_id" in prompt


def test_prime_verifiers_environment_filters_challenge_rows_by_split() -> None:
    module = _load_environment_module()

    heldout_rows = module.build_dataset_rows(
        target_family="LWE",
        seed_accepted=True,
        challenge_suite=True,
        challenge_split="heldout",
    )
    train_rows = module.build_dataset_rows(
        target_family="LWE",
        seed_accepted=True,
        challenge_suite=True,
        challenge_split="train",
    )

    assert heldout_rows
    assert train_rows
    assert all(row["info"]["heldout_split"] == "heldout" for row in heldout_rows)
    assert all(row["info"]["heldout_split"] == "train" for row in train_rows)
    assert len(heldout_rows) + len(train_rows) == len(
        module.build_dataset_rows(
            target_family="LWE",
            seed_accepted=True,
            challenge_suite=True,
        )
    )


def test_prime_verifiers_environment_rejects_challenge_split_without_suite() -> None:
    module = _load_environment_module()

    with pytest.raises(
        ValueError,
        match="challenge_split requires challenge_suite=True",
    ):
        module.build_dataset_rows(challenge_split="heldout")


def test_prime_verifiers_environment_rejects_unknown_challenge_split() -> None:
    module = _load_environment_module()

    with pytest.raises(ValueError, match="unsupported Prime challenge_split"):
        module.build_dataset_rows(
            target_family="LWE",
            seed_accepted=True,
            challenge_suite=True,
            challenge_split="validation",
        )


def test_prime_verifiers_environment_scores_challenge_against_target_metadata() -> None:
    module = _load_environment_module()
    raw_plan = Path(
        "prime_intellect/verifiers_environment/data/lattice_bdd_toy.json"
    ).read_text(encoding="utf-8")
    row = module.build_dataset_rows(
        attack_plan_id="lattice_bdd_toy_v1",
        challenge_suite=True,
        challenge_type="operator_mismatch_repair",
    )[0]
    task_metadata = row["info"]["task_metadata"]
    broken_plan = module._operator_mismatch_invalid_output(
        raw_plan,
        task_info=task_metadata,
    )
    original_operator = json.loads(raw_plan)["operators"][0]
    broken_operator = json.loads(broken_plan)["operators"][0]

    broken_report = module.score_attack_plan_completion_report(
        _assistant_completion(broken_plan),
        info=row["info"],
        require_info=True,
    )
    repaired_report = module.score_attack_plan_completion_report(
        _assistant_completion(raw_plan),
        info=row["info"],
        require_info=True,
    )

    assert broken_operator["type"] != original_operator["type"]
    assert broken_operator["params"] == original_operator["params"]
    assert broken_operator["assumptions"] == original_operator["assumptions"]
    assert "Repair only the wrong operator type" in row["prompt"][0]["content"]
    assert broken_report["accepted"] is False
    assert broken_report["aggregate_reward"] == 0.0
    assert repaired_report["accepted"] is True
    assert repaired_report["aggregate_reward"] == 1.0
    assert repaired_report["challenge"]["challenge_type"] == "operator_mismatch_repair"
    assert repaired_report["challenge"]["task_metadata"]["attack_plan_id"] == (
        "lattice_bdd_toy_v1"
    )


def test_prime_verifiers_environment_scores_missing_hypothesis_challenge() -> None:
    module = _load_environment_module()
    raw_plan = Path(
        "prime_intellect/verifiers_environment/data/lattice_bdd_toy.json"
    ).read_text(encoding="utf-8")
    row = module.build_dataset_rows(
        attack_plan_id="lattice_bdd_toy_v1",
        challenge_suite=True,
        challenge_type="missing_hypothesis_repair",
    )[0]
    broken_plan = module._missing_hypothesis_invalid_output(raw_plan)
    original_operator = json.loads(raw_plan)["operators"][0]
    broken_operator = json.loads(broken_plan)["operators"][0]

    broken_report = module.score_attack_plan_completion_report(
        _assistant_completion(broken_plan),
        info=row["info"],
        require_info=True,
    )
    repaired_report = module.score_attack_plan_completion_report(
        _assistant_completion(raw_plan),
        info=row["info"],
        require_info=True,
    )

    assert broken_operator["assumptions"] == []
    assert original_operator["assumptions"]
    assert "Restore the missing operator assumptions" in row["prompt"][0]["content"]
    assert broken_report["accepted"] is False
    assert broken_report["aggregate_reward"] == 0.0
    assert "task_match" in broken_report["blocking_reasons"]
    assert repaired_report["accepted"] is True
    assert repaired_report["aggregate_reward"] == 1.0
    assert repaired_report["challenge"]["challenge_type"] == (
        "missing_hypothesis_repair"
    )


def test_prime_verifiers_environment_scores_invented_complexity_challenge() -> None:
    module = _load_environment_module()
    raw_plan = Path(
        "prime_intellect/verifiers_environment/data/lattice_bdd_toy.json"
    ).read_text(encoding="utf-8")
    row = module.build_dataset_rows(
        attack_plan_id="lattice_bdd_toy_v1",
        challenge_suite=True,
        challenge_type="invented_complexity_repair",
    )[0]
    broken_plan = module._invented_complexity_invalid_output(raw_plan)
    broken_claims = json.loads(broken_plan)["claims"]

    broken_report = module.score_attack_plan_completion_report(
        _assistant_completion(broken_plan),
        info=row["info"],
        require_info=True,
    )
    repaired_report = module.score_attack_plan_completion_report(
        _assistant_completion(raw_plan),
        info=row["info"],
        require_info=True,
    )

    assert broken_claims["estimated_time_bits"] == 41.0
    assert broken_claims["external_claim"] is True
    assert "Remove the invented complexity claim" in row["prompt"][0]["content"]
    assert broken_report["accepted"] is False
    assert broken_report["aggregate_reward"] == 0.0
    assert "no_security_overclaim" in broken_report["blocking_reasons"]
    assert repaired_report["accepted"] is True
    assert repaired_report["aggregate_reward"] == 1.0
    assert repaired_report["challenge"]["challenge_type"] == (
        "invented_complexity_repair"
    )


def test_prime_verifiers_environment_scores_semantic_mutation_challenge() -> None:
    module = _load_environment_module()
    raw_plan = Path(
        "prime_intellect/verifiers_environment/data/lattice_bdd_toy.json"
    ).read_text(encoding="utf-8")
    row = module.build_dataset_rows(
        attack_plan_id="lattice_bdd_toy_v1",
        challenge_suite=True,
        challenge_type="semantic_mutation_repair",
    )[0]
    mutated_plan = module._correct_submission_for_challenge(raw_plan, row["info"])

    copied_report = module.score_attack_plan_completion_report(
        _assistant_completion(raw_plan),
        info=row["info"],
        require_info=True,
    )
    mutated_report = module.score_attack_plan_completion_report(
        _assistant_completion(mutated_plan),
        info=row["info"],
        require_info=True,
    )

    assert row["answer"] == "mutate_attackplan"
    assert row["info"]["expected_behavior"] == "mutate_attackplan"
    assert "Do not copy the Seed AttackPlan" in row["prompt"][0]["content"]
    assert "claims.estimated_time_bits=null" in row["prompt"][0]["content"]
    assert "Do not add top-level external_claim or source" in (
        row["prompt"][0]["content"]
    )
    assert copied_report["accepted"] is False
    assert copied_report["aggregate_reward"] == 0.0
    assert "semantic_mutation" in copied_report["blocking_reasons"]
    assert copied_report["benchmark_constraints"][
        "semantic_mutation_required"
    ] is True
    assert copied_report["benchmark_constraints"][
        "semantic_mutation_present"
    ] is False
    assert mutated_report["accepted"] is True
    assert mutated_report["aggregate_reward"] == 1.0
    assert mutated_report["benchmark_constraints"][
        "semantic_mutation_present"
    ] is True


def test_prime_verifiers_environment_scores_unsupported_refusal_challenge() -> None:
    module = _load_environment_module()
    raw_plan = Path(
        "prime_intellect/verifiers_environment/data/"
        "lattice_lwe_modulus_switching_primary.json"
    ).read_text(encoding="utf-8")
    row = module.build_dataset_rows(
        attack_plan_id="lattice_lwe_modulus_switching_primary_v1",
        challenge_suite=True,
        challenge_type="unsupported_refusal",
    )[0]
    task_metadata = row["info"]["task_metadata"]
    refusal = module._unsupported_refusal_for_task(task_metadata)
    copied_attackplan_report = module.score_attack_plan_completion_report(
        _assistant_completion(raw_plan),
        info=row["info"],
        require_info=True,
    )
    refusal_report = module.score_attack_plan_completion_report(
        _assistant_completion(json.dumps(refusal)),
        info=row["info"],
        require_info=True,
    )
    fake_attackplan_refusal = {
        **refusal,
        "attack_plan_id": "fake",
        "operators": [],
    }
    fake_report = module.score_attack_plan_completion_report(
        _assistant_completion(json.dumps(fake_attackplan_refusal)),
        info=row["info"],
        require_info=True,
    )

    assert copied_attackplan_report["accepted"] is False
    assert copied_attackplan_report["aggregate_reward"] == 0.0
    assert "unsupported_refusal_includes_attackplan_fields" in (
        copied_attackplan_report["blocking_reasons"]
    )
    assert refusal_report["accepted"] is True
    assert refusal_report["aggregate_reward"] == 1.0
    assert refusal_report["formal_artifact_binding"] == {
        "reason": "unsupported_refusal_not_attackplan",
        "review_governance_ok": True,
        "status": "not_applicable",
    }
    assert refusal_report["challenge"]["expected_behavior"] == "refuse_unsupported"
    assert fake_report["accepted"] is False
    assert "unsupported_refusal_includes_attackplan_fields" in fake_report[
        "blocking_reasons"
    ]


def test_prime_verifiers_environment_builds_challenge_scorecard() -> None:
    module = _load_environment_module()

    scorecard = module.build_challenge_scorecard(
        attack_plan_id="lattice_bdd_toy_v1"
    )

    assert scorecard["schema_version"] == "agades.pqc.prime.challenge_scorecard.v1"
    assert scorecard["accepted"] is True
    assert scorecard["scope"] == {
        "attack_plan_id": "lattice_bdd_toy_v1",
        "target_family": None,
        "challenge_type": None,
        "challenge_split": None,
        "min_challenge_examples_per_type": None,
        "public_only": True,
        "private_data_allowed": False,
        "security_claims_allowed": False,
    }
    assert scorecard["summary"]["challenge_rows"] == 6
    assert scorecard["summary"]["challenge_type_counts"] == {
        "claims_guard_repair": 1,
        "invented_complexity_repair": 1,
        "missing_hypothesis_repair": 1,
        "operator_mismatch_repair": 1,
        "semantic_mutation_repair": 1,
        "wrong_family_decoy_repair": 1,
    }
    assert scorecard["summary"]["broken_accept_count"] == 0
    assert scorecard["summary"]["repaired_accept_count"] == 6
    assert scorecard["summary"]["broken_score_max"] == 0.0
    assert scorecard["summary"]["repaired_score_min"] == 1.0
    assert {
        result["broken_failure_mode"] for result in scorecard["results"]
    } == {
        "task_mismatch_decoy",
        "invented_complexity_claim",
        "missing_operator_hypothesis",
        "unreviewed_pre_evaluation_claims",
        "operator_sequence_mismatch",
        "seed_semantic_copy",
    }


def test_prime_verifiers_environment_builds_unsupported_refusal_scorecard() -> None:
    module = _load_environment_module()

    scorecard = module.build_challenge_scorecard(
        attack_plan_id="lattice_lwe_modulus_switching_primary_v1",
        challenge_type="unsupported_refusal",
    )

    assert scorecard["accepted"] is True
    assert scorecard["summary"]["challenge_rows"] == 1
    assert scorecard["summary"]["challenge_type_counts"] == {
        "unsupported_refusal": 1
    }
    assert scorecard["summary"]["broken_accept_count"] == 0
    assert scorecard["summary"]["repaired_accept_count"] == 1
    assert scorecard["summary"]["broken_score_max"] == 0.0
    assert scorecard["summary"]["repaired_score_min"] == 1.0
    assert scorecard["results"][0]["broken_failure_mode"] == (
        "unsupported_attackplan_submitted"
    )


def test_prime_verifiers_environment_builds_heldout_challenge_scorecard() -> None:
    module = _load_environment_module()

    scorecard = module.build_challenge_scorecard(
        attack_plan_id=None,
        target_family="LWE",
        challenge_split="heldout",
    )

    assert scorecard["accepted"] is True
    assert scorecard["scope"]["challenge_split"] == "heldout"
    assert scorecard["summary"]["heldout_split_counts"] == {"heldout": 8}
    assert {result["heldout_split"] for result in scorecard["results"]} == {"heldout"}


def test_prime_scorecard_global_heldout_covers_unsupported_refusal() -> None:
    module = _load_environment_module()

    scorecard = module.build_challenge_scorecard(
        attack_plan_id=None,
        challenge_split="heldout",
    )

    assert scorecard["accepted"] is True
    assert scorecard["summary"]["challenge_type_counts"]["unsupported_refusal"] > 0
    assert scorecard["summary"]["broken_accept_count"] == 0
    stern_decoy_results = [
        result
        for result in scorecard["results"]
        if result["challenge_type"] == "wrong_family_decoy_repair"
        and result["attack_plan_id"] == "code_based_stern_toy_v1"
    ]
    assert stern_decoy_results
    assert all(
        result["broken_score"] == 0.0 and result["broken_accepted"] is False
        for result in stern_decoy_results
    )


def test_prime_verifiers_environment_builds_balanced_heldout_challenge_rows() -> None:
    module = _load_environment_module()

    rows = module.build_dataset_rows(
        challenge_suite=True,
        challenge_split="heldout",
        min_challenge_examples_per_type=8,
    )

    challenge_counts = Counter(row["info"]["challenge_type"] for row in rows)
    assert len(rows) == 56
    assert challenge_counts == {
        "claims_guard_repair": 8,
        "invented_complexity_repair": 8,
        "missing_hypothesis_repair": 8,
        "operator_mismatch_repair": 8,
        "semantic_mutation_repair": 8,
        "unsupported_refusal": 8,
        "wrong_family_decoy_repair": 8,
    }
    assert {row["info"]["heldout_split"] for row in rows} == {"heldout"}
    assert {
        row["info"]["split_policy"] for row in rows
    } == {"balanced_min_per_type_v1"}
    assert len(
        {
            (
                row["info"]["challenge_type"],
                row["info"]["task_metadata"]["attack_plan_id"],
            )
            for row in rows
        }
    ) == len(rows)
    report = module.score_attack_plan_completion_report(
        _assistant_completion(
            module._correct_submission_for_challenge(
                module._raw_json_for_task_info(rows[0]["info"]["task_metadata"]),
                rows[0]["info"],
            )
        ),
        info=rows[0]["info"],
        require_info=True,
    )
    assert report["challenge"]["split_policy"] == "balanced_min_per_type_v1"


def test_prime_verifiers_environment_rejects_too_small_balanced_num_examples() -> None:
    module = _load_environment_module()

    with pytest.raises(ValueError, match="balanced challenge suite size"):
        module.build_dataset_rows(
            num_examples=16,
            challenge_suite=True,
            challenge_split="heldout",
            min_challenge_examples_per_type=8,
        )


def test_prime_verifiers_environment_selects_challenge_row_indices_for_reruns() -> None:
    module = _load_environment_module()

    full_rows = module.build_dataset_rows(
        challenge_suite=True,
        challenge_split="heldout",
        min_challenge_examples_per_type=8,
    )
    selected_rows = module.build_dataset_rows(
        challenge_suite=True,
        challenge_split="heldout",
        min_challenge_examples_per_type=8,
        challenge_row_indices=[5, 24],
    )

    assert len(selected_rows) == 2
    assert [row["info"]["challenge_row_index"] for row in selected_rows] == [5, 24]
    assert selected_rows[0]["info"]["task_metadata"] == full_rows[5]["info"][
        "task_metadata"
    ]
    assert selected_rows[1]["info"]["task_metadata"] == full_rows[24]["info"][
        "task_metadata"
    ]


def test_prime_verifiers_environment_rejects_bad_challenge_row_index() -> None:
    module = _load_environment_module()

    with pytest.raises(ValueError, match="challenge_row_indices contains out-of-range"):
        module.build_dataset_rows(
            challenge_suite=True,
            challenge_split="heldout",
            min_challenge_examples_per_type=8,
            challenge_row_indices=[999],
        )


def test_prime_verifiers_environment_builds_balanced_heldout_scorecard() -> None:
    module = _load_environment_module()

    scorecard = module.build_challenge_scorecard(
        attack_plan_id=None,
        challenge_split="heldout",
        min_challenge_examples_per_type=8,
    )

    assert scorecard["accepted"] is True
    assert scorecard["scope"]["min_challenge_examples_per_type"] == 8
    assert scorecard["summary"]["challenge_rows"] == 56
    assert scorecard["summary"]["challenge_type_counts"] == {
        "claims_guard_repair": 8,
        "invented_complexity_repair": 8,
        "missing_hypothesis_repair": 8,
        "operator_mismatch_repair": 8,
        "semantic_mutation_repair": 8,
        "unsupported_refusal": 8,
        "wrong_family_decoy_repair": 8,
    }


def test_prime_verifiers_environment_rejects_empty_dataset_filter() -> None:
    module = _load_environment_module()

    try:
        module.build_dataset_rows(attack_plan_id="does_not_exist")
    except ValueError as exc:
        assert "task filter matched no rows" in str(exc)
    else:
        raise AssertionError("empty Prime task filter should be rejected")

    try:
        module.build_dataset_rows(
            attack_plan_id="lattice_primal_usvp_toy_v1",
            seed_accepted=False,
        )
    except ValueError as exc:
        assert "seed_accepted" in str(exc)
    else:
        raise AssertionError("contradictory Prime task filter should be rejected")


def _assistant_completion(content: str) -> list[dict[str, str]]:
    return [{"role": "assistant", "content": content}]


def _load_environment_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "agades_pqc_verifier_env_test",
        ENV_MODULE,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _task_info_for(module: ModuleType, attack_plan_id: str) -> dict[str, object]:
    for row in module.build_dataset_rows():
        info = row["info"]
        if info["attack_plan_id"] == attack_plan_id:
            return info
    raise AssertionError(f"missing task info for {attack_plan_id}")


def _file_digests(
    root: Path,
    *,
    suffix: str | None = None,
    ignored_parts: frozenset[str] = frozenset(),
) -> dict[str, str]:
    digests: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if not path.is_file() or ignored_parts.intersection(relative.parts):
            continue
        if suffix is not None and path.suffix != suffix:
            continue
        digests[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests
