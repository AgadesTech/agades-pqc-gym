from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from types import ModuleType

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
        0.20,
        0.20,
        0.20,
        0.05,
        0.15,
        0.08,
        0.03,
        0.03,
        0.04,
        0.02,
    ]


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
