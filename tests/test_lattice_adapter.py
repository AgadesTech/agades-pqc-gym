from pathlib import Path

import pytest

from agades_pqc_gym.core.attack_plan import AttackOperator, AttackPlan, Constraints
from agades_pqc_gym.families.lattice import adapter as lattice_adapter
from agades_pqc_gym.families.lattice.adapter import LatticeFamilyAdapter


def test_lattice_adapter_estimates_lwe_with_mock_estimator() -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_dual_hybrid_toy.json").read_text()
    )
    adapter = LatticeFamilyAdapter()

    result = adapter.estimate(plan)

    assert result.evaluation_status == "ok"
    assert result.estimator_name == "mock-lattice-estimator"
    assert result.attack_type == "dual_hybrid"
    assert result.time_bits is not None
    assert result.memory_bits is not None


def test_lattice_adapter_rejects_uncataloged_primary_runtime_operator() -> None:
    base_plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    plan = base_plan.model_copy(
        update={
            "attack_plan_id": "lattice_modulus_switching_only_toy_v1",
            "operators": [
                AttackOperator(
                    type="modulus_switching",
                    params={"q_prime": 128},
                    assumptions=["noise_model_preserved_approximately"],
                )
            ],
        }
    )
    adapter = LatticeFamilyAdapter()

    result = adapter.estimate(plan)

    assert result.evaluation_status == "unsupported"
    assert result.estimator_name == "lattice-family-router"
    assert result.attack_type == "modulus_switching"
    assert result.time_bits is None
    assert result.memory_bits is None
    assert result.warnings == [
        (
            "modulus_switching is a lattice runtime operator but is not a "
            "cataloged primary LWE/MLWE estimator route."
        )
    ]


@pytest.mark.parametrize(
    ("operator_type", "params"),
    [
        ("bkz_parameter_sweep", {"beta_min": 48, "beta_max": 72}),
        ("meet_in_the_middle", {"split_dimension": 16}),
        ("module_lattice_reduction_hypothesis", {"model": "toy_module_model"}),
        ("modulus_switching", {"q_prime": 128}),
        ("normal_form_transform", {}),
        ("sample_selection", {"sample_count": 32}),
        ("secret_guessing", {"guess_dimension": 8}),
    ],
)
def test_lwe_uncataloged_runtime_operators_are_auxiliary_not_primary_routes(
    operator_type: str,
    params: dict[str, int | str],
) -> None:
    base_plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    plan = base_plan.model_copy(
        update={
            "attack_plan_id": f"lwe_{operator_type}_only_toy_v1",
            "operators": [
                AttackOperator(
                    type=operator_type,
                    params=params,
                    assumptions=["runtime_operator_boundary_test"],
                )
            ],
        }
    )
    adapter = LatticeFamilyAdapter()

    result = adapter.estimate(plan)

    assert result.evaluation_status == "unsupported"
    assert result.estimator_name == "lattice-family-router"
    assert result.attack_type == operator_type
    assert result.time_bits is None
    assert result.memory_bits is None
    assert result.warnings == [
        (
            f"{operator_type} is a lattice runtime operator but is not a "
            "cataloged primary LWE/MLWE estimator route."
        )
    ]


def test_lattice_adapter_estimates_mlwe_cataloged_mock_route() -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_mlwe_module_hypothesis_toy.json")
        .read_text()
    )
    adapter = LatticeFamilyAdapter()

    result = adapter.estimate(plan)

    assert result.evaluation_status == "ok"
    assert result.estimator_name == "mock-lattice-estimator"
    assert result.attack_type == "bkz_parameter_sweep"
    assert result.time_bits is not None
    assert result.memory_bits is not None


def test_lattice_adapter_runs_downscaled_reproduction_smoke_when_required() -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    ).model_copy(
        update={
            "constraints": Constraints(
                max_memory_bits=80.0,
                max_time_bits=128.0,
                require_reproducibility_on_downscaled_instances=True,
            )
        }
    )
    adapter = LatticeFamilyAdapter()

    result = adapter.reproduce_downscaled(plan)

    assert result is not None
    assert result.attempted is True
    assert result.status == "estimator_reproduced"
    assert result.success is True
    assert result.score == 0.2
    assert any("not cryptanalytic evidence" in warning for warning in result.warnings)


def test_lattice_adapter_solves_declared_public_downscaled_lwe_fixture() -> None:
    plan = AttackPlan.model_validate_json(
        Path(
            "examples/attack_plans/lattice_downscaled_lwe_instance_solve_toy.json"
        ).read_text()
    )
    adapter = LatticeFamilyAdapter()

    result = adapter.reproduce_downscaled(plan)

    assert result is not None
    assert result.attempted is True
    assert result.status == "instance_solved"
    assert result.success is True
    assert result.score == 0.4
    assert any(
        "Solved a public downscaled LWE fixture" in warning
        for warning in result.warnings
    )
    assert any("not a security claim" in warning for warning in result.warnings)


def test_lattice_adapter_can_solve_packaged_fixture_without_repo_benchmark(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(lattice_adapter, "ROOT", tmp_path)
    plan = AttackPlan.model_validate_json(
        Path(
            "examples/attack_plans/lattice_downscaled_lwe_instance_solve_toy.json"
        ).read_text()
    )
    adapter = LatticeFamilyAdapter()

    result = adapter.reproduce_downscaled(plan)

    assert result is not None
    assert result.status == "instance_solved"
    assert result.success is True


def test_lattice_adapter_can_solve_second_packaged_fixture_without_repo_benchmark(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(lattice_adapter, "ROOT", tmp_path)
    plan = AttackPlan.model_validate_json(
        Path(
            "examples/attack_plans/lattice_downscaled_lwe_instance_solve_n5_q19_toy.json"
        ).read_text()
    )
    adapter = LatticeFamilyAdapter()

    result = adapter.reproduce_downscaled(plan)

    assert result is not None
    assert result.status == "instance_solved"
    assert result.success is True


def test_lattice_adapter_can_solve_ternary_packaged_fixture_without_repo_benchmark(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(lattice_adapter, "ROOT", tmp_path)
    plan = AttackPlan.model_validate_json(
        Path(
            "examples/attack_plans/lattice_downscaled_lwe_instance_solve_n6_q23_ternary_toy.json"
        ).read_text()
    )
    adapter = LatticeFamilyAdapter()

    result = adapter.reproduce_downscaled(plan)

    assert result is not None
    assert result.status == "instance_solved"
    assert result.success is True


def test_lattice_adapter_solves_declared_public_downscaled_mlwe_fixture() -> None:
    plan = AttackPlan.model_validate_json(
        Path(
            "examples/attack_plans/"
            "lattice_downscaled_mlwe_instance_solve_toy.json"
        ).read_text()
    )
    adapter = LatticeFamilyAdapter()

    result = adapter.reproduce_downscaled(plan)

    assert result is not None
    assert result.attempted is True
    assert result.status == "instance_solved"
    assert result.success is True
    assert result.score == 0.4
    assert any(
        "Solved a public downscaled MLWE fixture" in warning
        for warning in result.warnings
    )
    assert any("not a security claim" in warning for warning in result.warnings)


def test_lattice_adapter_can_solve_mlwe_packaged_fixture_without_repo_benchmark(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(lattice_adapter, "ROOT", tmp_path)
    plan = AttackPlan.model_validate_json(
        Path(
            "examples/attack_plans/"
            "lattice_downscaled_mlwe_instance_solve_toy.json"
        ).read_text()
    )
    adapter = LatticeFamilyAdapter()

    result = adapter.reproduce_downscaled(plan)

    assert result is not None
    assert result.status == "instance_solved"
    assert result.success is True


def test_lattice_adapter_rejects_downscaled_fixture_paths_outside_benchmarks() -> None:
    base_plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    plan = base_plan.model_copy(
        update={
            "constraints": Constraints(
                max_memory_bits=80.0,
                max_time_bits=128.0,
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture="../private_fixture.json",
            )
        }
    )
    adapter = LatticeFamilyAdapter()

    result = adapter.reproduce_downscaled(plan)

    assert result is not None
    assert result.attempted is False
    assert result.status == "not_applicable"
    assert result.success is False
    assert any(
        "benchmarks/lattice_downscaled_lwe_instances/" in warning
        for warning in result.warnings
    )


def test_lattice_adapter_rejects_downscaled_fixture_paths_outside_lwe_scope() -> None:
    base_plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    plan = base_plan.model_copy(
        update={
            "constraints": Constraints(
                max_memory_bits=80.0,
                max_time_bits=128.0,
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/lattice_toy_lwe/lwe_n64_q257.json"
                ),
            )
        }
    )
    adapter = LatticeFamilyAdapter()

    result = adapter.reproduce_downscaled(plan)

    assert result is not None
    assert result.attempted is False
    assert result.status == "not_applicable"
    assert result.success is False
    assert any(
        "benchmarks/lattice_downscaled_lwe_instances/" in warning
        for warning in result.warnings
    )


def test_lattice_adapter_refuses_private_downscaled_reproduction() -> None:
    base_plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    plan = base_plan.model_copy(
        update={
            "constraints": Constraints(
                max_memory_bits=80.0,
                max_time_bits=128.0,
                require_reproducibility_on_downscaled_instances=True,
            ),
            "metadata": base_plan.metadata.model_copy(update={"public": False}),
        }
    )
    adapter = LatticeFamilyAdapter()

    result = adapter.reproduce_downscaled(plan)

    assert result is not None
    assert result.attempted is False
    assert result.status == "not_applicable"
