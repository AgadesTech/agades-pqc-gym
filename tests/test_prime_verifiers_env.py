from __future__ import annotations

import hashlib
import importlib.util
import json
import tomllib
from pathlib import Path

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.integrations.task_metadata import TASK_METADATA_SCHEMA

ENV_DIR = Path("prime_intellect/verifiers_environment")
ENV_DATA_DIR = ENV_DIR / "data"
ENV_MODULE = ENV_DIR / "agades_pqc_verifier_env.py"
ENV_PYPROJECT = ENV_DIR / "pyproject.toml"


def _valid_public_attack_plan_paths() -> list[Path]:
    paths = []
    for path in sorted(Path("examples/attack_plans").glob("*.json")):
        try:
            plan = AttackPlan.model_validate_json(path.read_text())
        except ValueError:
            continue
        if plan.metadata.public:
            paths.append(path)
    return paths


def _load_env_module():
    spec = importlib.util.spec_from_file_location("agades_pqc_verifier_env", ENV_MODULE)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_prime_verifiers_pyproject_declares_installable_environment() -> None:
    data = tomllib.loads(ENV_PYPROJECT.read_text())

    project = data["project"]
    assert project["name"] == "agades-pqc-verifier-env"
    assert "verifiers>=0.1.8" in project["dependencies"]
    assert "hatchling" in data["build-system"]["requires"]
    assert data["tool"]["hatch"]["metadata"]["allow-direct-references"] is True
    assert data["tool"]["hatch"]["build"]["include"] == [
        "agades_pqc_verifier_env.py",
        "pyproject.toml",
        "README.md",
        "prime_manifest.json",
        "data/*.json",
        "docs/*.json",
        "formal/lean/**/*",
    ]
    assert data["tool"]["verifiers"]["eval"]["num_examples"] == 2
    assert data["tool"]["verifiers"]["eval"]["rollouts_per_example"] == 1


def test_prime_verifiers_embeds_seed_plans_for_standalone_install() -> None:
    source_paths = _valid_public_attack_plan_paths()
    packaged_names = sorted(path.name for path in ENV_DATA_DIR.glob("*.json"))

    assert packaged_names == sorted(path.name for path in source_paths)
    assert "invalid_plan_should_fail.json" not in packaged_names
    for source_path in source_paths:
        package_path = ENV_DATA_DIR / source_path.name
        assert package_path.read_text() == source_path.read_text()


def test_prime_verifiers_dataset_rows_cover_all_public_valid_families() -> None:
    module = _load_env_module()
    rows = module.build_dataset_rows()

    assert len(rows) == len(_valid_public_attack_plan_paths())
    first_prompt = rows[0]["prompt"][0]["content"]
    first_info = rows[0]["info"]
    families = {row["info"]["target_family"] for row in rows}

    assert families == {
        "CODE_BASED",
        "HASH_BASED",
        "IMPLEMENTATION_SECURITY",
        "ISOGENY_HISTORICAL",
        "LWE",
        "MLWE",
        "MULTIVARIATE",
        "NTRU",
        "SIS",
    }
    assert rows[0]["prompt"][0]["role"] == "user"
    assert "Submit exactly one AttackPlan JSON object" in first_prompt
    assert "Do not submit Python" in first_prompt
    assert module.PROMPT_PROFILES == (
        "attackplan_json",
        "format_first_copy_seed",
        "format_repair_extract_seed",
        "claims_guard_repair",
        "claims_guard_format_repair",
        "claims_guard_decoy_format_repair",
    )
    assert first_info["schema_version"] == TASK_METADATA_SCHEMA
    assert first_info["source_path"].startswith("data/")
    assert first_info["target_name"]
    assert first_info["operator_types"]
    assert first_info["public"] is True

    accepted_row = next(
        row
        for row in rows
        if row["info"]["attack_plan_id"] == "lattice_primal_usvp_toy_v1"
    )
    unsupported_row = next(
        row
        for row in rows
        if row["info"]["attack_plan_id"] == "lattice_ntru_schema_placeholder_v1"
    )
    runtime_boundary_row = next(
        row
        for row in rows
        if row["info"]["attack_plan_id"] == "lattice_lwe_modulus_switching_primary_v1"
    )
    assert accepted_row["answer"] == "accepted"
    assert accepted_row["info"]["seed_accepted"] is True
    assert accepted_row["info"]["seed_evaluation_status"] == "ok"
    assert accepted_row["info"]["seed_reward"] == 1.0
    assert runtime_boundary_row["answer"] == "unsupported"
    assert runtime_boundary_row["info"]["operator_types"] == ["modulus_switching"]
    assert runtime_boundary_row["info"]["seed_accepted"] is False
    assert runtime_boundary_row["info"]["seed_evaluation_status"] == "unsupported"
    assert runtime_boundary_row["info"]["seed_reward"] == 0.0
    assert unsupported_row["answer"] == "unsupported"
    assert unsupported_row["info"]["seed_accepted"] is False
    assert unsupported_row["info"]["seed_evaluation_status"] == "unsupported"
    assert unsupported_row["info"]["seed_reward"] == 0.0
    for row in rows:
        source_path = ENV_DIR / row["info"]["source_path"]
        expected_digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
        assert row["info"]["seed_attack_plan_sha256"] == expected_digest


def test_prime_verifiers_default_prompt_is_strict_json_boundary() -> None:
    module = _load_env_module()

    rows = module.build_dataset_rows(
        attack_plan_id="lattice_bkw_toy_v1",
        prompt_profile="attackplan_json",
    )

    prompt = rows[0]["prompt"][0]["content"]
    assert "If the Seed AttackPlan already satisfies the task, return it unchanged" in prompt
    assert "Do not include markdown, prose, analysis, comments, code fences, or wrapper text" in prompt
    assert "first non-whitespace character must be {" in prompt
    assert "final non-whitespace character must be }" in prompt
    assert "Seed AttackPlan:" in prompt


def test_prime_verifiers_dataset_respects_num_examples_limit() -> None:
    module = _load_env_module()

    rows = module.build_dataset_rows(num_examples=3)

    assert len(rows) == 3


def test_prime_verifiers_format_first_profile_instructs_seed_copy() -> None:
    module = _load_env_module()

    rows = module.build_dataset_rows(
        attack_plan_id="lattice_primal_usvp_toy_v1",
        prompt_profile="format_first_copy_seed",
    )

    prompt = rows[0]["prompt"][0]["content"]
    assert "Return the Seed AttackPlan below unchanged" in prompt
    assert "Preserve every field" in prompt
    assert "Do not add markdown" in prompt
    assert "first non-whitespace character must be {" in prompt
    assert rows[0]["info"]["attack_plan_id"] == "lattice_primal_usvp_toy_v1"


def test_prime_verifiers_format_repair_profile_instructs_json_extraction() -> None:
    module = _load_env_module()

    rows = module.build_dataset_rows(
        attack_plan_id="lattice_primal_usvp_toy_v1",
        prompt_profile="format_repair_extract_seed",
    )

    prompt = rows[0]["prompt"][0]["content"]
    assert "Repair the broken model output below." in prompt
    assert "markdown code fence" in prompt
    assert "Return only the corrected AttackPlan JSON object." in prompt
    assert "```json" in prompt
    assert rows[0]["info"]["attack_plan_id"] == "lattice_primal_usvp_toy_v1"


def test_prime_verifiers_claims_guard_profile_instructs_claim_repair() -> None:
    module = _load_env_module()

    rows = module.build_dataset_rows(
        attack_plan_id="lattice_bdd_toy_v1",
        prompt_profile="claims_guard_repair",
    )

    prompt = rows[0]["prompt"][0]["content"]
    assert "Repair the invalid AttackPlan JSON object below." in prompt
    assert "pre-evaluation estimates" in prompt
    assert "estimated_time_bits=null" in prompt
    assert "estimated_memory_bits=null" in prompt
    assert "success_probability=null" in prompt
    assert "Do not add external_claim or source" in prompt
    assert "```" not in prompt
    assert rows[0]["info"]["attack_plan_id"] == "lattice_bdd_toy_v1"


def test_prime_verifiers_claims_guard_format_repair_profile_combines_repairs() -> None:
    module = _load_env_module()

    rows = module.build_dataset_rows(
        attack_plan_id="lattice_bdd_toy_v1",
        prompt_profile="claims_guard_format_repair",
    )

    prompt = rows[0]["prompt"][0]["content"]
    assert "Repair the broken model output below." in prompt
    assert "markdown code fence" in prompt
    assert "pre-evaluation estimates" in prompt
    assert "estimated_time_bits=null" in prompt
    assert "estimated_memory_bits=null" in prompt
    assert "success_probability=null" in prompt
    assert "Do not add external_claim or source" in prompt
    assert "Return only the corrected AttackPlan JSON object." in prompt
    assert "```json" in prompt
    assert rows[0]["info"]["attack_plan_id"] == "lattice_bdd_toy_v1"


def test_prime_verifiers_claims_guard_decoy_format_repair_profile_is_harder() -> None:
    module = _load_env_module()

    rows = module.build_dataset_rows(
        attack_plan_id="lattice_bdd_toy_v1",
        prompt_profile="claims_guard_decoy_format_repair",
    )

    prompt = rows[0]["prompt"][0]["content"]
    assert "Ignore Candidate object 1" in prompt
    assert "AttackPlan-like decoy from a different task" in prompt
    assert "code_based_prange_toy_v1" in prompt
    assert "Candidate object 1" in prompt
    assert "Candidate object 2" in prompt
    assert "markdown code fence" in prompt
    assert "pre-evaluation estimates" in prompt
    assert "estimated_time_bits=null" in prompt
    assert "estimated_memory_bits=null" in prompt
    assert "success_probability=null" in prompt
    assert "Return only the corrected AttackPlan JSON object." in prompt
    assert "```json" in prompt
    assert rows[0]["info"]["attack_plan_id"] == "lattice_bdd_toy_v1"


def test_prime_verifiers_claims_guard_format_repair_scores_near_misses() -> None:
    module = _load_env_module()
    rows = module.build_dataset_rows(
        attack_plan_id="lattice_bdd_toy_v1",
        prompt_profile="claims_guard_format_repair",
    )
    row = rows[0]
    repaired_json = Path("examples/attack_plans/lattice_bdd_toy.json").read_text()
    invalid_claims_json = _with_unreviewed_claim_estimates(repaired_json)
    wrapped_repaired_json = "\n".join(
        [
            "Here is the candidate:",
            "```json",
            repaired_json,
            "```",
        ]
    )

    repaired_report = module.score_attack_plan_completion_report(
        _completion(repaired_json),
        info=row["info"],
        reward_profile="format_repair_dense",
    )
    invalid_claims_report = module.score_attack_plan_completion_report(
        _completion(invalid_claims_json),
        info=row["info"],
        reward_profile="format_repair_dense",
    )
    wrapped_report = module.score_attack_plan_completion_report(
        _completion(wrapped_repaired_json),
        info=row["info"],
        reward_profile="format_repair_dense",
    )

    assert repaired_report["accepted"] is True
    assert repaired_report["aggregate_reward"] == 1.0
    assert invalid_claims_report["accepted"] is False
    assert 0.0 < invalid_claims_report["aggregate_reward"] < 1.0
    assert invalid_claims_report["rubric_scores"]["single_json_object"] == 1.0
    assert wrapped_report["accepted"] is False
    assert wrapped_report["single_json_object"] is False
    assert (
        invalid_claims_report["aggregate_reward"]
        < wrapped_report["aggregate_reward"]
        < repaired_report["aggregate_reward"]
    )


def test_prime_verifiers_dataset_filters_seed_acceptance() -> None:
    module = _load_env_module()

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
    assert all(row["info"]["target_family"] == "LWE" for row in accepted_lwe_rows)
    assert all(row["info"]["seed_accepted"] is True for row in accepted_lwe_rows)
    assert all(row["info"]["seed_accepted"] is False for row in unsupported_lwe_rows)
    assert {
        row["info"]["attack_plan_id"]
        for row in unsupported_lwe_rows
    } >= {"lattice_lwe_modulus_switching_primary_v1"}


def test_prime_verifiers_rejects_unknown_prompt_profile() -> None:
    module = _load_env_module()

    try:
        module.build_dataset_rows(prompt_profile="unknown")
    except ValueError as exc:
        assert "unsupported Prime prompt profile" in str(exc)
    else:
        raise AssertionError("unknown Prime prompt profile should be rejected")


def test_prime_verifiers_reward_scores_public_verifier_results() -> None:
    module = _load_env_module()
    accepted_json = Path(
        "examples/attack_plans/lattice_primal_usvp_toy.json"
    ).read_text()
    unsupported_json = Path(
        "examples/attack_plans/code_based_isd_placeholder.json"
    ).read_text()
    invalid_json = '{"not": "an attack plan"}'
    prefixed_json = f"candidate:\n{accepted_json}"

    assert module.score_attack_plan_completion(_completion(accepted_json)) == 1.0
    assert module.score_attack_plan_completion(_completion(unsupported_json)) == 0.0
    assert module.score_attack_plan_completion(_completion(invalid_json)) == 0.0
    assert module.score_attack_plan_completion(_completion(prefixed_json)) == 0.0

    code_based_json = Path(
        "examples/attack_plans/code_based_prange_toy.json"
    ).read_text()
    code_based_second_json = Path(
        "examples/attack_plans/code_based_prange_toy_n15.json"
    ).read_text()
    code_based_stern_json = Path(
        "examples/attack_plans/code_based_stern_toy.json"
    ).read_text()
    code_based_lee_brickell_json = Path(
        "examples/attack_plans/code_based_lee_brickell_toy.json"
    ).read_text()
    code_based_qc_json = Path(
        "examples/attack_plans/code_based_qc_rotation_toy.json"
    ).read_text()
    code_based_hqc_parity_json = Path(
        "examples/attack_plans/code_based_hqc_parity_check_toy.json"
    ).read_text()
    code_based_hqc_circulant_json = Path(
        "examples/attack_plans/code_based_hqc_circulant_syndrome_toy.json"
    ).read_text()
    code_based_mdpc_black_gray_json = Path(
        "examples/attack_plans/code_based_mdpc_black_gray_toy.json"
    ).read_text()
    code_based_classic_mceliece_json = Path(
        "examples/attack_plans/code_based_classic_mceliece_syndrome_toy.json"
    ).read_text()
    hash_based_json = Path(
        "examples/attack_plans/hash_based_preimage_toy.json"
    ).read_text()
    hash_collision_json = Path(
        "examples/attack_plans/hash_based_collision_toy.json"
    ).read_text()
    hash_signature_json = Path(
        "examples/attack_plans/hash_based_signature_toy.json"
    ).read_text()
    hash_slh_dsa_json = Path(
        "examples/attack_plans/hash_based_slh_dsa_hypertree_toy.json"
    ).read_text()
    implementation_timing_json = Path(
        "examples/attack_plans/implementation_security_timing_toy.json"
    ).read_text()
    implementation_acvp_json = Path(
        "examples/attack_plans/implementation_security_acvp_toy.json"
    ).read_text()
    implementation_benchmark_json = Path(
        "examples/attack_plans/implementation_security_benchmark_toy.json"
    ).read_text()
    implementation_binary_size_json = Path(
        "examples/attack_plans/implementation_security_binary_size_toy.json"
    ).read_text()
    multivariate_json = Path(
        "examples/attack_plans/multivariate_mq_toy.json"
    ).read_text()
    multivariate_hybrid_json = Path(
        "examples/attack_plans/multivariate_mq_hybrid_toy.json"
    ).read_text()
    multivariate_degree_json = Path(
        "examples/attack_plans/multivariate_mq_degree_bound_toy.json"
    ).read_text()
    multivariate_degree_gf2_json = Path(
        "examples/attack_plans/multivariate_mq_degree_bound_gf2_toy.json"
    ).read_text()
    multivariate_minrank_json = Path(
        "examples/attack_plans/multivariate_minrank_toy.json"
    ).read_text()
    instance_solver_json = Path(
        "examples/attack_plans/lattice_downscaled_lwe_instance_solve_toy.json"
    ).read_text()
    second_instance_solver_json = Path(
        "examples/attack_plans/"
        "lattice_downscaled_lwe_instance_solve_n5_q19_toy.json"
    ).read_text()
    ntru_json = Path(
        "examples/attack_plans/lattice_ntru_schema_placeholder.json"
    ).read_text()
    sis_json = Path(
        "examples/attack_plans/lattice_sis_schema_placeholder.json"
    ).read_text()
    assert module.score_attack_plan_completion(_completion(code_based_json)) == 1.0
    assert (
        module.score_attack_plan_completion(_completion(code_based_second_json))
        == 1.0
    )
    assert (
        module.score_attack_plan_completion(_completion(code_based_stern_json))
        == 1.0
    )
    assert (
        module.score_attack_plan_completion(
            _completion(code_based_lee_brickell_json)
        )
        == 1.0
    )
    assert module.score_attack_plan_completion(_completion(code_based_qc_json)) == 1.0
    assert (
        module.score_attack_plan_completion(_completion(code_based_hqc_parity_json))
        == 1.0
    )
    assert (
        module.score_attack_plan_completion(
            _completion(code_based_hqc_circulant_json)
        )
        == 1.0
    )
    assert (
        module.score_attack_plan_completion(
            _completion(code_based_mdpc_black_gray_json)
        )
        == 1.0
    )
    assert (
        module.score_attack_plan_completion(
            _completion(code_based_classic_mceliece_json)
        )
        == 1.0
    )
    assert module.score_attack_plan_completion(_completion(hash_based_json)) == 1.0
    assert module.score_attack_plan_completion(_completion(hash_collision_json)) == 1.0
    assert module.score_attack_plan_completion(_completion(hash_signature_json)) == 1.0
    assert module.score_attack_plan_completion(_completion(hash_slh_dsa_json)) == 1.0
    assert (
        module.score_attack_plan_completion(_completion(implementation_timing_json))
        == 1.0
    )
    assert (
        module.score_attack_plan_completion(_completion(implementation_acvp_json))
        == 1.0
    )
    assert (
        module.score_attack_plan_completion(_completion(implementation_benchmark_json))
        == 1.0
    )
    assert (
        module.score_attack_plan_completion(
            _completion(implementation_binary_size_json)
        )
        == 1.0
    )
    assert module.score_attack_plan_completion(_completion(multivariate_json)) == 1.0
    assert (
        module.score_attack_plan_completion(_completion(multivariate_hybrid_json))
        == 1.0
    )
    assert (
        module.score_attack_plan_completion(_completion(multivariate_degree_json))
        == 1.0
    )
    assert (
        module.score_attack_plan_completion(
            _completion(multivariate_degree_gf2_json)
        )
        == 1.0
    )
    assert (
        module.score_attack_plan_completion(_completion(multivariate_minrank_json))
        == 1.0
    )
    assert module.score_attack_plan_completion(_completion(instance_solver_json)) == 1.0
    assert (
        module.score_attack_plan_completion(_completion(second_instance_solver_json))
        == 1.0
    )
    assert module.score_attack_plan_completion(_completion(ntru_json)) == 0.0
    assert module.score_attack_plan_completion(_completion(sis_json)) == 0.0


def test_prime_verifiers_reward_enforces_task_constraints() -> None:
    module = _load_env_module()
    rows = module.build_dataset_rows()
    lattice_row = next(
        row
        for row in rows
        if row["info"]["attack_plan_id"] == "lattice_primal_usvp_toy_v1"
    )
    lattice_json = Path(
        "examples/attack_plans/lattice_primal_usvp_toy.json"
    ).read_text()
    code_based_json = Path(
        "examples/attack_plans/code_based_prange_toy.json"
    ).read_text()
    mutated_lattice = json.loads(lattice_json)
    mutated_lattice["attack_plan_id"] = "candidate_lattice_primal_usvp_variant"

    assert (
        module.score_attack_plan_completion(
            _completion(json.dumps(mutated_lattice)),
            info=lattice_row["info"],
        )
        == 1.0
    )
    assert (
        module.score_attack_plan_completion(
            _completion(code_based_json),
            info=lattice_row["info"],
        )
        == 0.0
    )
    assert (
        module.score_attack_plan_completion(
            _completion(lattice_json),
            info=json.dumps(lattice_row["info"]),
        )
        == 1.0
    )
    assert (
        module.score_attack_plan_completion(
            _completion(lattice_json),
            require_info=True,
        )
        == 0.0
    )


def test_prime_verifiers_load_environment_reports_missing_optional_deps() -> None:
    module = _load_env_module()

    try:
        module.load_environment()
    except RuntimeError as exc:
        assert "verifiers" in str(exc)
        assert "datasets" in str(exc)


def _completion(content: str) -> list[dict[str, str]]:
    return [{"role": "assistant", "content": content}]


def _with_unreviewed_claim_estimates(raw_json: str) -> str:
    payload = json.loads(raw_json)
    claims = payload.setdefault("claims", {})
    claims["estimated_time_bits"] = 64.0
    claims["estimated_memory_bits"] = 32.0
    claims["success_probability"] = 0.5
    claims.pop("external_claim", None)
    claims.pop("source", None)
    return json.dumps(payload, indent=2, sort_keys=True)
