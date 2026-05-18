from __future__ import annotations

import importlib
import importlib.util
import json
import subprocess
import sys
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from agades_pqc_gym.core.attack_plan import AttackOperator, AttackPlan
from agades_pqc_gym.core.target import Distribution, TargetFamily, TargetSpec
from agades_pqc_gym.evaluators.base import EstimatorResult, EstimatorUnavailable
from agades_pqc_gym.evaluators.cache import JsonFileCache
from agades_pqc_gym.evaluators.lattice_estimator_checkout import (
    inspect_lattice_estimator_checkout,
)
from agades_pqc_gym.utils.commands import format_command, parse_command
from agades_pqc_gym.utils.hashing import stable_sha256
from agades_pqc_gym.validators.consistency import primary_attack_type

_ATTACK_TO_ESTIMATOR_KEY = {
    "primal_usvp": "usvp",
    "bounded_distance_decoding": "bdd",
    "dual_attack": "dual",
    "dual_hybrid": "dual_hybrid",
    "bkw": "bkw",
}

_ESTIMATOR_ALGORITHMS = frozenset(
    {
        "arora-gb",
        "bkw",
        "usvp",
        "bdd",
        "bdd_hybrid",
        "bdd_mitm_hybrid",
        "dual",
        "dual_hybrid",
    }
)
LATTICE_ESTIMATOR_PINNED_COMMIT = "6019056011d10d7e9c30a0d5da2d2f729fbc2eec"


class LatticeEstimatorBackend(Protocol):
    version: str | None
    commit: str | None

    def make_binary_distribution(self) -> Any: ...

    def make_sparse_binary_distribution(self, hamming_weight: int) -> Any: ...

    def make_centered_binomial_distribution(self, eta: int) -> Any: ...

    def make_discrete_gaussian_distribution(self, sigma: float) -> Any: ...

    def make_lwe_parameters(
        self,
        *,
        n: int,
        q: int,
        xs: Any,
        xe: Any,
        m: int,
        tag: str,
    ) -> Any: ...

    def estimate_lwe(
        self,
        *,
        params: Any,
        algorithm_key: str,
        red_cost_model: str | None,
        red_shape_model: str | None,
        jobs: int,
        catch_exceptions: bool,
    ) -> dict[str, Any]: ...


@dataclass(frozen=True)
class LatticeEstimatorConfig:
    jobs: int = 1
    catch_exceptions: bool = True
    red_shape_model: str | None = None
    required_commit: str | None = LATTICE_ESTIMATOR_PINNED_COMMIT


class LatticeEstimatorAdapter:
    """Reviewed boundary for real Lattice Estimator calls.

    The adapter only maps explicit LWE-family operators to known Lattice
    Estimator algorithm keys. Unsupported operators return structured
    `unsupported` results rather than falling back to the mock estimator.
    """

    estimator_name = "lattice-estimator"

    def __init__(
        self,
        *,
        backend: LatticeEstimatorBackend | None = None,
        cache_path: Path | None = None,
        config: LatticeEstimatorConfig | None = None,
        source_path: Path | None = None,
    ) -> None:
        self._backend = backend
        self._cache = JsonFileCache(cache_path) if cache_path else None
        self._config = config or LatticeEstimatorConfig()
        self._source_path = source_path

    def is_available(self) -> bool:
        if self._source_path is not None:
            return self._source_path.exists()
        return (
            self._backend is not None
            or importlib.util.find_spec("estimator") is not None
        )

    def estimate(self, plan: AttackPlan) -> EstimatorResult:
        attack_type = primary_attack_type(plan)
        algorithm_key = _ATTACK_TO_ESTIMATOR_KEY.get(attack_type)
        if algorithm_key is None:
            return _unsupported_result(
                plan=plan,
                attack_type=attack_type,
                warning=(
                    f"{attack_type} is not mapped to a reviewed Lattice Estimator "
                    "algorithm key"
                ),
            )

        cache_key = self._cache_key(plan, algorithm_key)
        cached = self._cache.get(cache_key) if self._cache else None
        if cached:
            return EstimatorResult.model_validate(cached)

        try:
            backend = self._load_backend()
            pin_warning = _backend_pin_warning(backend, self._config.required_commit)
            if pin_warning is not None:
                return _error_result(
                    plan=plan,
                    attack_type=attack_type,
                    warning=pin_warning,
                    estimator_version=backend.version,
                    estimator_commit=backend.commit,
                )
            params, mapping_warnings = _build_lwe_parameters(
                plan.target,
                backend,
            )
            primary_operator = _primary_operator(plan, attack_type)
            raw_results = backend.estimate_lwe(
                params=params,
                algorithm_key=algorithm_key,
                red_cost_model=_red_cost_model(primary_operator),
                red_shape_model=self._config.red_shape_model,
                jobs=self._config.jobs,
                catch_exceptions=self._config.catch_exceptions,
            )
        except EstimatorUnavailable as exc:
            return _error_result(plan=plan, attack_type=attack_type, warning=str(exc))
        except Exception as exc:
            return _error_result(
                plan=plan,
                attack_type=attack_type,
                warning=f"Lattice Estimator call failed: {exc}",
            )

        algorithm_result = raw_results.get(algorithm_key)
        if not isinstance(algorithm_result, dict):
            return _unsupported_result(
                plan=plan,
                attack_type=attack_type,
                warning=(
                    "Lattice Estimator did not return a result for "
                    f"{algorithm_key}"
                ),
            )

        result = EstimatorResult(
            estimator_name=self.estimator_name,
            estimator_version=backend.version,
            estimator_commit=backend.commit,
            evaluation_status="ok",
            attack_type=attack_type,
            time_bits=_optional_float(algorithm_result.get("rop")),
            memory_bits=_optional_float(
                algorithm_result.get("mem", algorithm_result.get("red"))
            ),
            raw_output={
                "algorithm_key": algorithm_key,
                "target_mapping": _target_mapping(plan.target),
                "estimator_result": _json_safe(algorithm_result),
            },
            warnings=mapping_warnings
            + [
                "Lattice Estimator output is an analytical estimate and requires "
                "independent review before any security claim."
            ],
        )
        if result.time_bits is None:
            return _error_result(
                plan=plan,
                attack_type=attack_type,
                warning="Lattice Estimator result did not include numeric rop cost",
            )
        if result.memory_bits is None:
            result.memory_bits = 0.0
            result.warnings.append(
                "Lattice Estimator result did not include memory cost; recorded 0.0"
            )
        if self._cache:
            self._cache.set(cache_key, result.model_dump(mode="json"))
        return result

    def _load_backend(self) -> LatticeEstimatorBackend:
        if self._backend is not None:
            return self._backend
        if self._source_path is not None:
            self._backend = ImportedLatticeEstimatorBackend(
                source_path=self._source_path,
                required_commit=self._config.required_commit,
            )
            return self._backend
        if not self.is_available():
            raise EstimatorUnavailable(
                "Lattice Estimator Python module is not importable in this "
                "environment"
            )
        return ImportedLatticeEstimatorBackend()

    def _cache_key(self, plan: AttackPlan, algorithm_key: str) -> str:
        return stable_sha256(
            {
                "adapter": self.estimator_name,
                "algorithm_key": algorithm_key,
                "config": self._config.__dict__,
                "source_path": str(self._source_path) if self._source_path else None,
                "plan": plan.model_dump(mode="json"),
            }
        )


def reviewed_lwe_estimator_mappings() -> dict[str, str]:
    """Return reviewed direct LWE AttackPlan operator to estimator-key mappings."""
    return dict(_ATTACK_TO_ESTIMATOR_KEY)


def _backend_pin_warning(
    backend: LatticeEstimatorBackend,
    required_commit: str | None,
) -> str | None:
    if required_commit is None:
        return None
    if backend.commit is None:
        return (
            "Lattice Estimator backend does not expose commit metadata; reviewed "
            f"pin {required_commit} cannot be verified"
        )
    if backend.commit != required_commit:
        return (
            f"Lattice Estimator backend commit {backend.commit} does not match "
            f"reviewed pin {required_commit}"
        )
    return None


class ImportedLatticeEstimatorBackend:
    def __init__(
        self,
        *,
        source_path: Path | None = None,
        required_commit: str | None = None,
    ) -> None:
        estimator, commit = _load_estimator_module(
            source_path=source_path,
            required_commit=required_commit,
        )
        self._estimator = estimator
        self.version = getattr(estimator, "__version__", None)
        self.commit = commit

    def make_binary_distribution(self) -> Any:
        return self._estimator.ND.Binary

    def make_sparse_binary_distribution(self, hamming_weight: int) -> Any:
        return self._estimator.ND.SparseBinary(hamming_weight)

    def make_centered_binomial_distribution(self, eta: int) -> Any:
        return self._estimator.ND.CenteredBinomial(eta)

    def make_discrete_gaussian_distribution(self, sigma: float) -> Any:
        return self._estimator.ND.DiscreteGaussian(sigma)

    def make_lwe_parameters(
        self,
        *,
        n: int,
        q: int,
        xs: Any,
        xe: Any,
        m: int,
        tag: str,
    ) -> Any:
        return self._estimator.LWE.Parameters(
            n=n,
            q=q,
            Xs=xs,
            Xe=xe,
            m=m,
            tag=tag,
        )

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
        deny_list = tuple(sorted(_ESTIMATOR_ALGORITHMS - {algorithm_key}))
        kwargs: dict[str, Any] = {
            "deny_list": deny_list,
            "jobs": jobs,
            "catch_exceptions": catch_exceptions,
            "quiet": True,
        }
        if red_cost_model is not None:
            kwargs["red_cost_model"] = _resolve_reduction_cost_model(
                self._estimator,
                red_cost_model,
            )
        if red_shape_model is not None:
            kwargs["red_shape_model"] = red_shape_model
        return self._estimator.LWE.estimate(params, **kwargs)


class SageSubprocessLatticeEstimatorBackend:
    """Run a reviewed local Lattice Estimator checkout under `sage -python`."""

    def __init__(
        self,
        *,
        sage_command: str,
        sage_python_command: str | None = None,
        source_path: Path,
        required_commit: str | None = LATTICE_ESTIMATOR_PINNED_COMMIT,
        timeout_seconds: int = 120,
    ) -> None:
        self._sage_command = sage_command
        self._sage_python_command_parts = (
            parse_command(sage_python_command, label="sage_python_command")
            if sage_python_command is not None
            else [*parse_command(sage_command, label="sage_command"), "-python"]
        )
        self._sage_python_command_display = format_command(
            self._sage_python_command_parts
        )
        self._source_path = source_path.resolve()
        self._required_commit = required_commit
        self._timeout_seconds = timeout_seconds
        self.version: str | None = None

        inspection = inspect_lattice_estimator_checkout(
            self._source_path,
            required_commit=required_commit,
        )
        self.commit = inspection.head_commit
        self._inspection_failures = list(inspection.failures)

    def make_binary_distribution(self) -> dict[str, Any]:
        return {"type": "binary"}

    def make_sparse_binary_distribution(self, hamming_weight: int) -> dict[str, Any]:
        return {"type": "sparse_binary", "hamming_weight": hamming_weight}

    def make_centered_binomial_distribution(self, eta: int) -> dict[str, Any]:
        return {"type": "centered_binomial", "eta": eta}

    def make_discrete_gaussian_distribution(self, sigma: float) -> dict[str, Any]:
        return {"type": "discrete_gaussian", "sigma": sigma}

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
        return {"n": n, "q": q, "Xs": xs, "Xe": xe, "m": m, "tag": tag}

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
        if self._inspection_failures:
            raise EstimatorUnavailable(self._inspection_failures[0])
        request = {
            "source_path": self._source_path.as_posix(),
            "algorithm_key": algorithm_key,
            "estimator_algorithms": sorted(_ESTIMATOR_ALGORITHMS),
            "params": params,
            "red_cost_model": red_cost_model,
            "red_shape_model": red_shape_model,
            "jobs": jobs,
            "catch_exceptions": catch_exceptions,
        }
        worker = Path(__file__).with_name("lattice_estimator_sage_worker.py")
        try:
            completed = subprocess.run(
                [*self._sage_python_command_parts, worker.as_posix()],
                input=json.dumps(request, sort_keys=True),
                text=True,
                capture_output=True,
                check=False,
                timeout=self._timeout_seconds,
            )
        except FileNotFoundError as exc:
            raise EstimatorUnavailable(
                f"Sage Python command not found: {self._sage_python_command_display}"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise EstimatorUnavailable(
                "Lattice Estimator Sage subprocess timed out after "
                f"{self._timeout_seconds} seconds: "
                f"{_subprocess_output_summary(exc.stdout, exc.stderr)}"
            ) from exc

        if completed.returncode != 0:
            raise EstimatorUnavailable(
                "Lattice Estimator Sage subprocess failed with exit code "
                f"{completed.returncode}: "
                f"{_subprocess_output_summary(completed.stdout, completed.stderr)}"
            )
        try:
            response = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise EstimatorUnavailable(
                "Lattice Estimator Sage subprocess returned invalid JSON: "
                f"{_subprocess_output_summary(completed.stdout, completed.stderr)}"
            ) from exc
        if not isinstance(response, dict):
            raise EstimatorUnavailable(
                "Lattice Estimator Sage subprocess returned a non-object payload."
            )
        if response.get("ok") is not True:
            error = response.get("error")
            raise EstimatorUnavailable(
                "Lattice Estimator Sage subprocess failed: "
                f"{error if isinstance(error, str) else 'unknown error'}"
            )
        version = response.get("version")
        self.version = version if isinstance(version, str) else None
        result = response.get("result")
        if not isinstance(result, dict):
            raise EstimatorUnavailable(
                "Lattice Estimator Sage subprocess returned invalid result payload."
            )
        return result


def _load_estimator_module(
    *,
    source_path: Path | None,
    required_commit: str | None,
) -> tuple[Any, str | None]:
    if source_path is None:
        try:
            import estimator
        except Exception as exc:
            raise EstimatorUnavailable(
                "Lattice Estimator Python module failed to import: "
                f"{_exception_summary(exc)}"
            ) from exc
        return estimator, getattr(estimator, "__commit__", None)

    resolved_source = source_path.resolve()
    inspection = inspect_lattice_estimator_checkout(
        resolved_source,
        required_commit=required_commit,
    )
    if not inspection.ready:
        raise EstimatorUnavailable(inspection.failures[0])
    return _import_estimator_from_checkout(resolved_source), inspection.head_commit


def _import_estimator_from_checkout(source_path: Path) -> Any:
    if not (
        (source_path / "estimator" / "__init__.py").is_file()
        or (source_path / "estimator.py").is_file()
    ):
        raise EstimatorUnavailable(
            "Local Lattice Estimator checkout does not contain an estimator "
            "package or module"
        )

    existing = sys.modules.get("estimator")
    if existing is not None:
        raise EstimatorUnavailable(
            "Lattice Estimator module is already imported; start a fresh "
            "process before using --estimator-source so the checkout commit can "
            "be tied to the imported code"
        )

    sys.path.insert(0, str(source_path))
    try:
        module = importlib.import_module("estimator")
    except Exception as exc:
        sys.modules.pop("estimator", None)
        raise EstimatorUnavailable(
            "Local Lattice Estimator checkout failed to import estimator: "
            f"{_exception_summary(exc)}"
        ) from exc
    finally:
        with suppress(ValueError):
            sys.path.remove(str(source_path))

    if not _module_file_is_under_path(module, source_path):
        sys.modules.pop("estimator", None)
        raise EstimatorUnavailable(
            "Local Lattice Estimator checkout did not resolve the estimator "
            "module from the requested source path"
        )
    return module


def _exception_summary(exc: Exception) -> str:
    message = " ".join(str(exc).split())
    if not message:
        return exc.__class__.__name__
    return f"{exc.__class__.__name__}: {message}"


def _subprocess_output_summary(
    stdout: str | bytes | None,
    stderr: str | bytes | None,
) -> str:
    parts = [
        _decode_output(output).strip()
        for output in (stdout, stderr)
        if output is not None and _decode_output(output).strip()
    ]
    summary = " ".join(" ".join(parts).split())
    return summary[:240] if summary else "no output"


def _decode_output(output: str | bytes) -> str:
    if isinstance(output, bytes):
        return output.decode("utf-8", errors="replace")
    return output


def _module_file_is_under_path(module: Any, source_path: Path) -> bool:
    module_file = getattr(module, "__file__", None)
    if not isinstance(module_file, str):
        return False
    try:
        Path(module_file).resolve().relative_to(source_path)
    except ValueError:
        return False
    return True


def _build_lwe_parameters(
    target: TargetSpec,
    backend: LatticeEstimatorBackend,
) -> tuple[Any, list[str]]:
    if target.family not in {TargetFamily.LWE, TargetFamily.MLWE}:
        raise EstimatorUnavailable(
            f"Lattice Estimator adapter does not support {target.family.value}"
        )
    if target.n is None or target.q is None or target.secret_distribution is None:
        raise EstimatorUnavailable("LWE/MLWE target is missing required parameters")
    if target.error_distribution is None:
        raise EstimatorUnavailable("LWE/MLWE target is missing error_distribution")

    warnings: list[str] = []
    dimension = target.n
    sample_count = target.m or target.n
    if target.family is TargetFamily.MLWE:
        if target.k is None:
            raise EstimatorUnavailable("MLWE target is missing module rank k")
        dimension = target.n * target.k
        sample_count = target.m or dimension
        warnings.append(
            "MLWE target was flattened to an LWE parameter set with dimension n*k; "
            "this analytical mapping requires expert review."
        )

    return (
        backend.make_lwe_parameters(
            n=dimension,
            q=target.q,
            xs=_distribution_to_estimator(
                target.secret_distribution,
                backend,
            ),
            xe=_distribution_to_estimator(
                target.error_distribution,
                backend,
            ),
            m=sample_count,
            tag=target.name,
        ),
        warnings,
    )


def _distribution_to_estimator(
    distribution: Distribution,
    backend: LatticeEstimatorBackend,
) -> Any:
    if distribution.type == "binary":
        if distribution.hamming_weight is not None:
            return backend.make_sparse_binary_distribution(distribution.hamming_weight)
        return backend.make_binary_distribution()
    if distribution.type == "centered_binomial":
        if distribution.eta is None:
            raise EstimatorUnavailable("centered_binomial requires eta")
        return backend.make_centered_binomial_distribution(distribution.eta)
    if distribution.type == "discrete_gaussian":
        if distribution.sigma is None:
            raise EstimatorUnavailable("discrete_gaussian requires sigma")
        return backend.make_discrete_gaussian_distribution(distribution.sigma)
    raise EstimatorUnavailable(
        f"distribution type {distribution.type} is not mapped to Lattice Estimator"
    )


def _primary_operator(plan: AttackPlan, attack_type: str) -> AttackOperator | None:
    for operator in reversed(plan.operators):
        if operator.type == attack_type:
            return operator
    return None


def _red_cost_model(operator: AttackOperator | None) -> str | None:
    if operator is None:
        return None
    model = operator.params.get("svp_cost_model")
    return model if isinstance(model, str) else None


def _resolve_reduction_cost_model(estimator: Any, model_name: str) -> Any:
    try:
        return getattr(estimator.RC, model_name)
    except AttributeError as exc:
        raise EstimatorUnavailable(
            f"unknown Lattice Estimator reduction cost model: {model_name}"
        ) from exc


def _target_mapping(target: TargetSpec) -> dict[str, Any]:
    dimension = target.n
    if (
        target.family is TargetFamily.MLWE
        and target.n is not None
        and target.k is not None
    ):
        dimension = target.n * target.k
    return {
        "family": target.family.value,
        "lwe_dimension": dimension,
        "q": target.q,
        "m": target.m,
        "tag": target.name,
    }


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)


def _unsupported_result(
    *,
    plan: AttackPlan,
    attack_type: str,
    warning: str,
) -> EstimatorResult:
    return EstimatorResult(
        estimator_name="lattice-estimator-router",
        estimator_version=None,
        estimator_commit=None,
        evaluation_status="unsupported",
        attack_type=attack_type,
        time_bits=None,
        memory_bits=None,
        warnings=[warning],
        raw_output={"target": plan.target.model_dump(mode="json")},
    )


def _error_result(
    *,
    plan: AttackPlan,
    attack_type: str,
    warning: str,
    estimator_version: str | None = None,
    estimator_commit: str | None = None,
) -> EstimatorResult:
    return EstimatorResult(
        estimator_name=LatticeEstimatorAdapter.estimator_name,
        estimator_version=estimator_version,
        estimator_commit=estimator_commit,
        evaluation_status="error",
        attack_type=attack_type,
        time_bits=None,
        memory_bits=None,
        warnings=[warning],
        raw_output={"target": plan.target.model_dump(mode="json")},
    )
