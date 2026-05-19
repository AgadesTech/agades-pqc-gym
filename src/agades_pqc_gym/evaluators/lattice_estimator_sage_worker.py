from __future__ import annotations

import importlib
import json
import sys
from contextlib import suppress
from pathlib import Path
from typing import Any


def main() -> None:
    try:
        request = json.loads(sys.stdin.read())
        response = _handle_request(request)
    except Exception as exc:  # noqa: BLE001 - worker must return diagnostics.
        response = {"ok": False, "error": _exception_summary(exc)}
    sys.stdout.write(json.dumps(response, sort_keys=True))


def _handle_request(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("request must be a JSON object")
    source_path = _path_field(request, "source_path")
    algorithm_key = _string_field(request, "algorithm_key")
    estimator_algorithms = _string_list_field(request, "estimator_algorithms")
    params_request = _object_field(request, "params")
    estimator = _import_estimator(source_path)

    params = estimator.LWE.Parameters(
        n=_int_field(params_request, "n"),
        q=_int_field(params_request, "q"),
        Xs=_distribution_to_estimator(estimator, _object_field(params_request, "Xs")),
        Xe=_distribution_to_estimator(estimator, _object_field(params_request, "Xe")),
        m=_int_field(params_request, "m"),
        tag=_string_field(params_request, "tag"),
    )
    kwargs: dict[str, Any] = {
        "deny_list": tuple(
            sorted(set(estimator_algorithms) - {algorithm_key})
        ),
        "jobs": _int_field(request, "jobs"),
        "catch_exceptions": _bool_field(request, "catch_exceptions"),
        "quiet": True,
    }
    red_cost_model = request.get("red_cost_model")
    if isinstance(red_cost_model, str):
        kwargs["red_cost_model"] = getattr(estimator.RC, red_cost_model)
    red_shape_model = request.get("red_shape_model")
    if isinstance(red_shape_model, str):
        kwargs["red_shape_model"] = red_shape_model

    return {
        "ok": True,
        "version": getattr(estimator, "__version__", None),
        "result": _json_safe(estimator.LWE.estimate(params, **kwargs)),
    }


def _import_estimator(source_path: Path) -> Any:
    existing = sys.modules.get("estimator")
    if existing is not None:
        raise RuntimeError("estimator module is already imported")
    sys.path.insert(0, source_path.as_posix())
    try:
        module = importlib.import_module("estimator")
    finally:
        with suppress(ValueError):
            sys.path.remove(source_path.as_posix())
    if not _module_file_is_under_path(module, source_path):
        sys.modules.pop("estimator", None)
        raise RuntimeError("estimator module did not resolve from source_path")
    return module


def _distribution_to_estimator(estimator: Any, distribution: dict[str, Any]) -> Any:
    distribution_type = _string_field(distribution, "type")
    if distribution_type == "binary":
        return estimator.ND.Binary
    if distribution_type == "sparse_binary":
        return estimator.ND.SparseBinary(_int_field(distribution, "hamming_weight"))
    if distribution_type == "centered_binomial":
        return estimator.ND.CenteredBinomial(_int_field(distribution, "eta"))
    if distribution_type == "discrete_gaussian":
        return estimator.ND.DiscreteGaussian(_float_field(distribution, "sigma"))
    raise ValueError(f"unsupported distribution type: {distribution_type}")


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if _has_mapping_interface(value):
        keys = value.keys()
        return {str(key): _json_safe(value[key]) for key in keys}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)


def _has_mapping_interface(value: Any) -> bool:
    return callable(getattr(value, "keys", None)) and callable(
        getattr(value, "__getitem__", None)
    )


def _path_field(payload: dict[str, Any], field: str) -> Path:
    return Path(_string_field(payload, field)).resolve()


def _object_field(payload: dict[str, Any], field: str) -> dict[str, Any]:
    value = payload.get(field)
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _string_field(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    return value


def _string_list_field(payload: dict[str, Any], field: str) -> list[str]:
    value = payload.get(field)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field} must be a list of strings")
    return value


def _int_field(payload: dict[str, Any], field: str) -> int:
    value = payload.get(field)
    if not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
    return value


def _float_field(payload: dict[str, Any], field: str) -> float:
    value = payload.get(field)
    if not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be numeric")
    return float(value)


def _bool_field(payload: dict[str, Any], field: str) -> bool:
    value = payload.get(field)
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be a boolean")
    return value


def _module_file_is_under_path(module: Any, source_path: Path) -> bool:
    module_file = getattr(module, "__file__", None)
    if not isinstance(module_file, str):
        return False
    try:
        Path(module_file).resolve().relative_to(source_path)
    except ValueError:
        return False
    return True


def _exception_summary(exc: Exception) -> str:
    message = " ".join(str(exc).split())
    if not message:
        return exc.__class__.__name__
    return f"{exc.__class__.__name__}: {message}"


if __name__ == "__main__":
    main()
