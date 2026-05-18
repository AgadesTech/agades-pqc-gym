from __future__ import annotations

import importlib
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

import pytest

from agades_pqc_gym.core.attack_plan import AttackOperator, AttackPlan
from agades_pqc_gym.evaluators.lattice_estimator import (
    LATTICE_ESTIMATOR_PINNED_COMMIT,
    LatticeEstimatorAdapter,
    LatticeEstimatorConfig,
    SageSubprocessLatticeEstimatorBackend,
)


class FakeLatticeEstimatorBackend:
    version = "fake-0.1"
    commit = LATTICE_ESTIMATOR_PINNED_COMMIT

    def __init__(self) -> None:
        self.calls = 0
        self.last_params: dict[str, Any] | None = None
        self.last_algorithm_key: str | None = None
        self.last_red_cost_model: str | None = None

    def make_binary_distribution(self) -> tuple[str]:
        return ("binary",)

    def make_sparse_binary_distribution(self, hamming_weight: int) -> tuple[str, int]:
        return ("sparse_binary", hamming_weight)

    def make_centered_binomial_distribution(self, eta: int) -> tuple[str, int]:
        return ("centered_binomial", eta)

    def make_discrete_gaussian_distribution(self, sigma: float) -> tuple[str, float]:
        return ("discrete_gaussian", sigma)

    def make_lwe_parameters(
        self,
        *,
        n: int,
        q: int,
        xs: Any,
        xe: Any,
        m: int,
        tag: str,
    ) -> dict[str, Any]:
        self.last_params = {"n": n, "q": q, "xs": xs, "xe": xe, "m": m, "tag": tag}
        return self.last_params

    def estimate_lwe(
        self,
        *,
        params: Any,
        algorithm_key: str,
        red_cost_model: str | None,
        red_shape_model: str | None,
        jobs: int,
        catch_exceptions: bool,
    ) -> dict[str, Any]:
        del params, red_shape_model, jobs, catch_exceptions
        self.calls += 1
        self.last_algorithm_key = algorithm_key
        self.last_red_cost_model = red_cost_model
        return {
            algorithm_key: {
                "rop": 57.25,
                "mem": 19.5,
                "beta": 72,
                "tag": algorithm_key,
            }
        }


def _clear_estimator_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "estimator" or module_name.startswith("estimator."):
            del sys.modules[module_name]


def _write_fake_lattice_estimator_checkout(tmp_path: Path) -> tuple[Path, str]:
    source = tmp_path / "fake-lattice-estimator"
    package = source / "estimator"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        textwrap.dedent(
            """
            from pathlib import Path

            Path(__file__).with_name("IMPORT_MARKER").write_text(
                "imported",
                encoding="utf-8",
            )
            __version__ = "fake-checkout-0.1"

            class ND:
                Binary = ("binary",)

                @staticmethod
                def SparseBinary(hamming_weight):
                    return ("sparse_binary", hamming_weight)

                @staticmethod
                def CenteredBinomial(eta):
                    return ("centered_binomial", eta)

                @staticmethod
                def DiscreteGaussian(sigma):
                    return ("discrete_gaussian", sigma)

            class RC:
                ADPS16 = "ADPS16"

            class LWE:
                @staticmethod
                def Parameters(*, n, q, Xs, Xe, m, tag):
                    return {"n": n, "q": q, "Xs": Xs, "Xe": Xe, "m": m, "tag": tag}

                @staticmethod
                def estimate(params, **kwargs):
                    del params
                    algorithms = {
                        "arora-gb",
                        "bkw",
                        "usvp",
                        "bdd",
                        "bdd_hybrid",
                        "bdd_mitm_hybrid",
                        "dual",
                        "dual_hybrid",
                    }
                    deny_list = set(kwargs.get("deny_list", ()))
                    algorithm_key = sorted(algorithms - deny_list)[0]
                    return {algorithm_key: {"rop": 63.5, "mem": 21.0, "beta": 73}}
            """
        ).lstrip(),
        encoding="utf-8",
    )
    subprocess.run(["git", "init"], cwd=source, check=True, capture_output=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "https://github.com/malb/lattice-estimator"],
        cwd=source,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "add", "estimator/__init__.py"],
        cwd=source,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=tests@example.com",
            "-c",
            "user.name=Agades Tests",
            "commit",
            "-m",
            "Add fake estimator package",
        ],
        cwd=source,
        check=True,
        capture_output=True,
    )
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=source,
        text=True,
    ).strip()
    return source, commit


def _write_fake_sage_python_runner(tmp_path: Path) -> Path:
    executable = tmp_path / "sage"
    executable.write_text(
        textwrap.dedent(
            """
            #!/usr/bin/env python3
            import os
            import pathlib
            import sys

            if sys.argv[1:2] == ["-python"]:
                marker = os.environ.get("AGADES_FAKE_SAGE_MARKER")
                if marker:
                    pathlib.Path(marker).write_text("used", encoding="utf-8")
                os.execv(sys.executable, [sys.executable, *sys.argv[2:]])
            raise SystemExit(f"unexpected fake sage invocation: {sys.argv[1:]}")
            """
        ).lstrip(),
        encoding="utf-8",
    )
    executable.chmod(0o755)
    return executable


def test_lattice_estimator_adapter_maps_primal_usvp_to_lwe_estimator() -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    backend = FakeLatticeEstimatorBackend()
    adapter = LatticeEstimatorAdapter(backend=backend)

    result = adapter.estimate(plan)

    assert result.evaluation_status == "ok"
    assert result.estimator_name == "lattice-estimator"
    assert result.estimator_version == "fake-0.1"
    assert result.estimator_commit == LATTICE_ESTIMATOR_PINNED_COMMIT
    assert result.attack_type == "primal_usvp"
    assert result.time_bits == 57.25
    assert result.memory_bits == 19.5
    assert backend.last_algorithm_key == "usvp"
    assert backend.last_red_cost_model == "ADPS16"
    assert backend.last_params == {
        "n": 64,
        "q": 257,
        "xs": ("binary",),
        "xe": ("discrete_gaussian", 2.8),
        "m": 128,
        "tag": "toy_lwe_n64_q257",
    }


def test_lattice_estimator_adapter_imports_pin_checked_local_checkout(
    tmp_path: Path,
) -> None:
    source, commit = _write_fake_lattice_estimator_checkout(tmp_path)
    _clear_estimator_modules()
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    adapter = LatticeEstimatorAdapter(
        source_path=source,
        config=LatticeEstimatorConfig(required_commit=commit),
    )

    result = adapter.estimate(plan)

    assert result.evaluation_status == "ok"
    assert result.estimator_name == "lattice-estimator"
    assert result.estimator_version == "fake-checkout-0.1"
    assert result.estimator_commit == commit
    assert result.time_bits == 63.5
    assert result.memory_bits == 21.0
    assert (source / "estimator" / "IMPORT_MARKER").read_text() == "imported"


def test_lattice_estimator_adapter_runs_local_checkout_under_sage_python(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, commit = _write_fake_lattice_estimator_checkout(tmp_path)
    sage = _write_fake_sage_python_runner(tmp_path)
    sage_marker = tmp_path / "sage-python-used"
    monkeypatch.setenv("AGADES_FAKE_SAGE_MARKER", sage_marker.as_posix())
    _clear_estimator_modules()
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    backend = SageSubprocessLatticeEstimatorBackend(
        sage_command=sage.as_posix(),
        source_path=source,
        required_commit=commit,
    )
    adapter = LatticeEstimatorAdapter(
        backend=backend,
        config=LatticeEstimatorConfig(required_commit=commit),
    )

    result = adapter.estimate(plan)

    assert result.evaluation_status == "ok"
    assert result.estimator_name == "lattice-estimator"
    assert result.estimator_version == "fake-checkout-0.1"
    assert result.estimator_commit == commit
    assert result.time_bits == 63.5
    assert result.memory_bits == 21.0
    assert sage_marker.read_text(encoding="utf-8") == "used"
    assert (source / "estimator" / "IMPORT_MARKER").read_text() == "imported"


def test_lattice_estimator_adapter_rejects_preimported_local_checkout(
    tmp_path: Path,
) -> None:
    source, commit = _write_fake_lattice_estimator_checkout(tmp_path)
    _clear_estimator_modules()
    sys.path.insert(0, str(source))
    try:
        importlib.import_module("estimator")
    finally:
        sys.path.remove(str(source))
    (source / "estimator" / "IMPORT_MARKER").unlink()
    shutil.rmtree(source / "estimator" / "__pycache__", ignore_errors=True)
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    adapter = LatticeEstimatorAdapter(
        source_path=source,
        config=LatticeEstimatorConfig(required_commit=commit),
    )

    try:
        result = adapter.estimate(plan)
    finally:
        _clear_estimator_modules()

    assert result.evaluation_status == "error"
    assert result.estimator_commit is None
    assert "already imported" in result.warnings[0]
    assert not (source / "estimator" / "IMPORT_MARKER").exists()


def test_lattice_estimator_adapter_rejects_local_checkout_before_import_on_pin_mismatch(
    tmp_path: Path,
) -> None:
    source, commit = _write_fake_lattice_estimator_checkout(tmp_path)
    _clear_estimator_modules()
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    adapter = LatticeEstimatorAdapter(
        source_path=source,
        config=LatticeEstimatorConfig(required_commit="0" * 40),
    )

    result = adapter.estimate(plan)

    assert result.evaluation_status == "error"
    assert result.estimator_commit is None
    assert result.time_bits is None
    assert result.memory_bits is None
    assert result.warnings == [
        (
            f"Local Lattice Estimator checkout commit {commit} does not match "
            "reviewed pin 0000000000000000000000000000000000000000."
        )
    ]
    assert not (source / "estimator" / "IMPORT_MARKER").exists()


def test_lattice_estimator_adapter_rejects_dirty_local_checkout_before_import(
    tmp_path: Path,
) -> None:
    source, commit = _write_fake_lattice_estimator_checkout(tmp_path)
    (source / "README.md").write_text("unreviewed local edit\n", encoding="utf-8")
    _clear_estimator_modules()
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    adapter = LatticeEstimatorAdapter(
        source_path=source,
        config=LatticeEstimatorConfig(required_commit=commit),
    )

    result = adapter.estimate(plan)

    assert result.evaluation_status == "error"
    assert result.estimator_commit is None
    assert result.time_bits is None
    assert result.memory_bits is None
    assert result.warnings == [
        "Local Lattice Estimator checkout working tree is not clean."
    ]
    assert not (source / "estimator" / "IMPORT_MARKER").exists()


def test_lattice_estimator_adapter_rejects_wrong_origin_before_import(
    tmp_path: Path,
) -> None:
    source, commit = _write_fake_lattice_estimator_checkout(tmp_path)
    subprocess.run(
        ["git", "remote", "set-url", "origin", "https://example.com/fork.git"],
        cwd=source,
        check=True,
        capture_output=True,
    )
    _clear_estimator_modules()
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    adapter = LatticeEstimatorAdapter(
        source_path=source,
        config=LatticeEstimatorConfig(required_commit=commit),
    )

    result = adapter.estimate(plan)

    assert result.evaluation_status == "error"
    assert result.estimator_commit is None
    assert result.time_bits is None
    assert result.memory_bits is None
    assert result.warnings == [
        (
            "Local Lattice Estimator checkout origin remote "
            "https://example.com/fork.git does not match reviewed upstream "
            "https://github.com/malb/lattice-estimator."
        )
    ]
    assert not (source / "estimator" / "IMPORT_MARKER").exists()


def test_lattice_estimator_adapter_rejects_local_checkout_without_git_metadata(
    tmp_path: Path,
) -> None:
    source, _ = _write_fake_lattice_estimator_checkout(tmp_path)
    no_git_source = tmp_path / "not-a-git-checkout"
    no_git_source.mkdir()
    (no_git_source / "estimator").mkdir()
    (no_git_source / "estimator" / "__init__.py").write_text(
        (source / "estimator" / "__init__.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    _clear_estimator_modules()
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    adapter = LatticeEstimatorAdapter(source_path=no_git_source)

    result = adapter.estimate(plan)

    assert result.evaluation_status == "error"
    assert result.estimator_commit is None
    assert "could not verify local Lattice Estimator checkout commit" in (
        result.warnings[0]
    )
    assert not (no_git_source / "estimator" / "IMPORT_MARKER").exists()


def test_lattice_estimator_adapter_records_local_checkout_import_failure_reason(
    tmp_path: Path,
) -> None:
    source, commit = _write_fake_lattice_estimator_checkout(tmp_path)
    (source / "estimator" / "__init__.py").write_text(
        "import definitely_missing_lattice_estimator_dependency\n",
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "add", "estimator/__init__.py"],
        cwd=source,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=tests@example.com",
            "-c",
            "user.name=Agades Tests",
            "commit",
            "-m",
            "Make fake estimator import fail",
        ],
        cwd=source,
        check=True,
        capture_output=True,
    )
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=source,
        text=True,
    ).strip()
    _clear_estimator_modules()
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    adapter = LatticeEstimatorAdapter(
        source_path=source,
        config=LatticeEstimatorConfig(required_commit=commit),
    )

    result = adapter.estimate(plan)

    assert result.evaluation_status == "error"
    assert result.estimator_commit is None
    assert result.time_bits is None
    assert result.memory_bits is None
    assert result.warnings == [
        (
            "Local Lattice Estimator checkout failed to import estimator: "
            "ModuleNotFoundError: No module named "
            "'definitely_missing_lattice_estimator_dependency'"
        )
    ]


def test_lattice_estimator_adapter_rejects_unpinned_backend_commit() -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    backend = FakeLatticeEstimatorBackend()
    backend.commit = "not-the-reviewed-pin"
    adapter = LatticeEstimatorAdapter(backend=backend)

    result = adapter.estimate(plan)

    assert result.evaluation_status == "error"
    assert result.estimator_name == "lattice-estimator"
    assert result.estimator_commit == "not-the-reviewed-pin"
    assert result.attack_type == "primal_usvp"
    assert result.time_bits is None
    assert result.memory_bits is None
    assert backend.calls == 0
    assert result.warnings == [
        (
            "Lattice Estimator backend commit not-the-reviewed-pin does not match "
            "reviewed pin 6019056011d10d7e9c30a0d5da2d2f729fbc2eec"
        )
    ]


def test_lattice_estimator_adapter_rejects_backend_without_commit_metadata() -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    backend = FakeLatticeEstimatorBackend()
    backend.commit = None
    adapter = LatticeEstimatorAdapter(backend=backend)

    result = adapter.estimate(plan)

    assert result.evaluation_status == "error"
    assert result.estimator_name == "lattice-estimator"
    assert result.estimator_commit is None
    assert result.attack_type == "primal_usvp"
    assert backend.calls == 0
    assert result.warnings == [
        (
            "Lattice Estimator backend does not expose commit metadata; reviewed "
            "pin 6019056011d10d7e9c30a0d5da2d2f729fbc2eec cannot be verified"
        )
    ]


def test_lattice_estimator_adapter_maps_bdd_operator_to_lwe_estimator() -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    ).model_copy(
        update={
            "operators": [
                AttackOperator(
                    type="bounded_distance_decoding",
                    params={"beta": 70, "svp_cost_model": "ADPS16"},
                    assumptions=[
                        "toy instance only",
                        "BDD estimate requires independent review",
                    ],
                )
            ],
            "attack_plan_id": "lattice_bdd_toy_v1",
        }
    )
    backend = FakeLatticeEstimatorBackend()
    adapter = LatticeEstimatorAdapter(backend=backend)

    result = adapter.estimate(plan)

    assert result.evaluation_status == "ok"
    assert result.attack_type == "bounded_distance_decoding"
    assert result.raw_output["algorithm_key"] == "bdd"
    assert backend.last_algorithm_key == "bdd"
    assert backend.last_red_cost_model == "ADPS16"


@pytest.mark.parametrize(
    ("example_path", "attack_type", "algorithm_key"),
    [
        (
            "examples/attack_plans/lattice_dual_attack_toy.json",
            "dual_attack",
            "dual",
        ),
        (
            "examples/attack_plans/lattice_bkw_toy.json",
            "bkw",
            "bkw",
        ),
    ],
)
def test_lattice_estimator_adapter_maps_public_direct_lwe_examples(
    example_path: str,
    attack_type: str,
    algorithm_key: str,
) -> None:
    plan = AttackPlan.model_validate_json(Path(example_path).read_text())
    backend = FakeLatticeEstimatorBackend()
    adapter = LatticeEstimatorAdapter(backend=backend)

    result = adapter.estimate(plan)

    assert result.evaluation_status == "ok"
    assert result.attack_type == attack_type
    assert result.raw_output["algorithm_key"] == algorithm_key
    assert backend.last_algorithm_key == algorithm_key


def test_lattice_estimator_adapter_caches_successful_results(tmp_path: Path) -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    backend = FakeLatticeEstimatorBackend()
    adapter = LatticeEstimatorAdapter(
        backend=backend,
        cache_path=tmp_path / "lattice-estimator-cache.json",
    )

    first = adapter.estimate(plan)
    second = adapter.estimate(plan)

    assert first == second
    assert backend.calls == 1


def test_lattice_estimator_adapter_rejects_unmapped_lattice_operator() -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_mlwe_module_hypothesis_toy.json").read_text()
    )
    adapter = LatticeEstimatorAdapter(backend=FakeLatticeEstimatorBackend())

    result = adapter.estimate(plan)

    assert result.evaluation_status == "unsupported"
    assert result.attack_type == "bkz_parameter_sweep"
    assert "not mapped" in result.warnings[0]
