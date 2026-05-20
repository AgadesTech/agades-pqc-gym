from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

ENV_MODULE = Path(
    "prime_intellect/verifiers_environment/agades_pqc_verifier_env.py"
)
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
    assert report["rubric_scores"] == {
        "accepted_attack_plan": 1.0,
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


def test_prime_verifiers_environment_builds_named_rubric_functions() -> None:
    module = _load_environment_module()

    functions = module.build_rubric_functions()

    assert [func.__name__ for func in functions] == list(module.PRIME_RUBRIC_TERMS)


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
