from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.formal.artifacts import REVIEWER_GOVERNANCE_BINDING_SCHEMA
from agades_pqc_gym.rl.environment import FORMAL_ARTIFACT_BINDING_SCHEMA

PRIME_ENVIRONMENT_SMOKE_SCHEMA = "agades.pqc.prime_environment_smoke.v1"
PRIME_ENVIRONMENT_SMOKE_VERIFICATION_SCHEMA = (
    "agades.pqc.prime_environment_smoke_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REPORT = Path("reports/prime_environment_smoke.json")
ENVIRONMENT_DIR = Path("prime_intellect/verifiers_environment")
ENVIRONMENT_MODULE_PATH = ENVIRONMENT_DIR / "agades_pqc_verifier_env.py"
ENVIRONMENT_ENTRYPOINT = "agades_pqc_verifier_env:load_environment"

_RELEASE_GATES = (
    "uv run pytest tests/test_prime_environment_smoke.py -q",
    "uv run agades-pqc prime-environment-smoke --out "
    "reports/prime_environment_smoke.json",
    "uv run agades-pqc prime-environment-smoke-verify --report "
    "reports/prime_environment_smoke.json",
    "uv build prime_intellect/verifiers_environment",
    "uv run agades-pqc ecosystem-smoke-verify --report reports/ecosystem_smoke.json",
    "uv run agades-pqc release-audit --out public/release_audit.json",
)
_FALSE_SAFETY_FLAGS = (
    "arbitrary_code_execution",
    "contains_private_traces",
    "live_targeting",
    "publishes_private_candidates",
    "security_claim",
)
_REQUIRED_OPTIONAL_PACKAGES = ("datasets", "verifiers")
_DEFAULT_ATTACK_PLAN_ID = "lattice_primal_usvp_toy_v1"


def build_prime_environment_smoke_report(
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    env_root = project_root / ENVIRONMENT_DIR
    module_path = project_root / ENVIRONMENT_MODULE_PATH
    failures: list[str] = []
    environment = {
        "environment_dir": ENVIRONMENT_DIR.as_posix(),
        "entrypoint": ENVIRONMENT_ENTRYPOINT,
        "imports_without_verifiers": False,
        "module_path": ENVIRONMENT_MODULE_PATH.as_posix(),
    }
    dataset = {
        "data_file_count": 0,
        "dataset_rows": 0,
        "default_attack_plan_id": _DEFAULT_ATTACK_PLAN_ID,
        "families": [],
        "mirrors_packaged_data": False,
    }
    scoring = {
        "accepted_score": None,
        "accepted_rubric_scores": {},
        "invalid_json_score": None,
        "formal_artifact_binding_schema": None,
        "prefixed_json_score": None,
        "requires_single_json_object": False,
        "review_governance_binding_schema": None,
        "review_governance_ok": False,
        "reviewer_quality": None,
        "rubric_terms": [],
        "unsupported_score": None,
    }
    optional_dependencies = {
        "load_environment_boundary_ok": False,
        "required_packages": list(_REQUIRED_OPTIONAL_PACKAGES),
    }

    try:
        module = _load_python_module(module_path, "agades_pqc_prime_environment_smoke")
        environment["imports_without_verifiers"] = True
        rows = module.build_dataset_rows()
        data_file_count = len(sorted((env_root / "data").glob("*.json")))
        accepted_json = (
            env_root / "data" / "lattice_primal_usvp_toy.json"
        ).read_text(encoding="utf-8")
        unsupported_json = (
            env_root / "data" / "code_based_isd_placeholder.json"
        ).read_text(encoding="utf-8")
        accepted_report = module.score_attack_plan_completion_report(
            _assistant_completion(accepted_json),
            info=_info_for_attack_plan_id(rows, _DEFAULT_ATTACK_PLAN_ID),
            require_info=True,
        )
        unsupported_score = module.score_attack_plan_completion(
            _assistant_completion(unsupported_json),
            info=_info_for_attack_plan_id(rows, "code_based_isd_placeholder_v1"),
            require_info=True,
        )
        invalid_json_score = module.score_attack_plan_completion(
            _assistant_completion('{"not": "an attack plan"}')
        )
        prefixed_json_score = module.score_attack_plan_completion(
            _assistant_completion(f"candidate:\n{accepted_json}")
        )
        formal_binding = _dict_or_empty(
            accepted_report.get("formal_artifact_binding")
        )
        review_governance = _dict_or_empty(
            formal_binding.get("review_governance")
        )
    except Exception as exc:  # noqa: BLE001 - smoke report must capture failures.
        failures.append(f"Prime environment smoke failed: {exc}")
    else:
        dataset = {
            "data_file_count": data_file_count,
            "dataset_rows": len(rows),
            "default_attack_plan_id": _DEFAULT_ATTACK_PLAN_ID,
            "families": sorted(
                {
                    info["target_family"]
                    for row in rows
                    if isinstance((info := row.get("info")), dict)
                    and isinstance(info.get("target_family"), str)
                }
            ),
            "mirrors_packaged_data": _rows_mirror_packaged_data(rows, data_file_count),
        }
        scoring = {
            "accepted_score": accepted_report["aggregate_reward"],
            "accepted_rubric_scores": accepted_report["rubric_scores"],
            "formal_artifact_binding_schema": formal_binding.get("schema_version"),
            "invalid_json_score": invalid_json_score,
            "prefixed_json_score": prefixed_json_score,
            "requires_single_json_object": prefixed_json_score == 0.0,
            "review_governance_binding_schema": review_governance.get(
                "schema_version"
            ),
            "review_governance_ok": accepted_report.get("review_governance_ok"),
            "reviewer_quality": accepted_report["rubric_scores"].get(
                "reviewer_quality"
            ),
            "rubric_terms": list(module.PRIME_RUBRIC_TERMS),
            "unsupported_score": unsupported_score,
        }
        optional_dependencies = {
            "load_environment_boundary_ok": _optional_dependency_boundary(module),
            "required_packages": list(_REQUIRED_OPTIONAL_PACKAGES),
        }
        if not _rows_include_attack_plan_id(rows, _DEFAULT_ATTACK_PLAN_ID):
            failures.append("Prime environment default AttackPlan row is missing.")
        _validate_smoke_contract(
            environment,
            dataset,
            scoring,
            optional_dependencies,
            failures,
        )

    return {
        "schema_version": PRIME_ENVIRONMENT_SMOKE_SCHEMA,
        "accepted": not failures,
        "environment": environment,
        "dataset": dataset,
        "scoring": scoring,
        "optional_dependencies": optional_dependencies,
        "safety": dict.fromkeys(_FALSE_SAFETY_FLAGS, False),
        "release_gates": list(_RELEASE_GATES),
        "failures": failures,
    }


def write_prime_environment_smoke_report(
    out: Path = DEFAULT_REPORT,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    report = build_prime_environment_smoke_report(root=root)
    resolved_out = _resolve_path(out, root=root)
    resolved_out.parent.mkdir(parents=True, exist_ok=True)
    resolved_out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def verify_prime_environment_smoke_report(
    report_path: Path = DEFAULT_REPORT,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    expected = build_prime_environment_smoke_report(root=project_root)
    failures: list[str] = []
    report = _read_report(_resolve_path(report_path, root=project_root), failures)

    if report != expected:
        failures.append("Prime environment smoke report is not in sync.")
    _verify_schema(report, failures)
    _verify_environment(report, failures)
    _verify_dataset(report, failures)
    _verify_scoring(report, failures)
    _verify_optional_dependencies(report, failures)
    _verify_safety(report, failures)
    _verify_release_gates(report, failures)

    return {
        "schema_version": PRIME_ENVIRONMENT_SMOKE_VERIFICATION_SCHEMA,
        "report_path": _display_path(report_path, root=project_root),
        "accepted": not failures,
        "summary": _verification_summary(report, failures),
        "failures": failures,
    }


def _validate_smoke_contract(
    environment: dict[str, Any],
    dataset: dict[str, Any],
    scoring: dict[str, Any],
    optional_dependencies: dict[str, Any],
    failures: list[str],
) -> None:
    if environment["imports_without_verifiers"] is not True:
        failures.append("Prime environment module did not import without Verifiers.")
    if dataset["dataset_rows"] < 1:
        failures.append("Prime environment builds no dataset rows.")
    if dataset["data_file_count"] != dataset["dataset_rows"]:
        failures.append("Prime environment data files do not match dataset rows.")
    if dataset["mirrors_packaged_data"] is not True:
        failures.append("Prime environment rows do not mirror packaged data.")
    if dataset["default_attack_plan_id"] != _DEFAULT_ATTACK_PLAN_ID:
        failures.append("Prime environment default AttackPlan id drifted.")
    if scoring["accepted_score"] != 1.0:
        failures.append("Prime environment rejects accepted toy plan.")
    if scoring["formal_artifact_binding_schema"] != FORMAL_ARTIFACT_BINDING_SCHEMA:
        failures.append("Prime environment formal artifact binding schema drifted.")
    if (
        scoring["review_governance_binding_schema"]
        != REVIEWER_GOVERNANCE_BINDING_SCHEMA
    ):
        failures.append("Prime environment reviewer governance schema drifted.")
    if scoring["review_governance_ok"] is not True:
        failures.append("Prime environment lacks reviewer governance.")
    if scoring["reviewer_quality"] != 1.0:
        failures.append("Prime environment reviewer quality failed.")
    if scoring["rubric_terms"] != [
        "accepted_attack_plan",
        "single_json_object",
        "formal_validity",
        "cryptographic_applicability",
        "no_security_overclaim",
        "student_readability",
        "reproducibility",
        "reviewer_quality",
        "task_match",
        "proof_obligation_coverage",
    ]:
        failures.append("Prime environment rubric terms drifted.")
    accepted_rubric_scores = scoring["accepted_rubric_scores"]
    if (
        not isinstance(accepted_rubric_scores, dict)
        or set(accepted_rubric_scores) != set(scoring["rubric_terms"])
        or any(score != 1.0 for score in accepted_rubric_scores.values())
    ):
        failures.append("Prime environment accepted rubric scores are incomplete.")
    if scoring["unsupported_score"] != 0.0:
        failures.append("Prime environment accepts unsupported plan.")
    if scoring["invalid_json_score"] != 0.0:
        failures.append("Prime environment accepts invalid JSON.")
    if scoring["prefixed_json_score"] != 0.0:
        failures.append("Prime environment accepts prefixed JSON.")
    if scoring["requires_single_json_object"] is not True:
        failures.append("Prime environment does not require a single JSON object.")
    if optional_dependencies["load_environment_boundary_ok"] is not True:
        failures.append("Prime environment optional dependency boundary failed.")


def _rows_mirror_packaged_data(
    rows: list[dict[str, Any]],
    data_file_count: int,
) -> bool:
    source_paths = []
    for row in rows:
        info = row.get("info")
        if not isinstance(info, dict):
            return False
        source_path = info.get("source_path")
        if not isinstance(source_path, str) or not source_path.startswith("data/"):
            return False
        source_paths.append(source_path)
    return len(source_paths) == data_file_count and len(set(source_paths)) == len(rows)


def _rows_include_attack_plan_id(
    rows: list[dict[str, Any]],
    attack_plan_id: str,
) -> bool:
    return any(
        isinstance((info := row.get("info")), dict)
        and info.get("attack_plan_id") == attack_plan_id
        for row in rows
    )


def _optional_dependency_boundary(module: Any) -> bool:
    try:
        module.load_environment(num_examples=1)
    except RuntimeError as exc:
        message = str(exc)
        return all(package in message for package in _REQUIRED_OPTIONAL_PACKAGES)
    return True


def _read_report(path: Path, failures: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"Prime environment smoke report is missing: {path}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(
            f"Prime environment smoke report is invalid JSON at line {exc.lineno}."
        )
        return {}
    if not isinstance(payload, dict):
        failures.append("Prime environment smoke report must be a JSON object.")
        return {}
    return payload


def _verify_schema(report: dict[str, Any], failures: list[str]) -> None:
    if report.get("schema_version") != PRIME_ENVIRONMENT_SMOKE_SCHEMA:
        failures.append(
            "Prime environment smoke report schema_version must be "
            f"{PRIME_ENVIRONMENT_SMOKE_SCHEMA}."
        )
    if report.get("accepted") is not True:
        failures.append("Prime environment smoke report is not accepted.")


def _verify_environment(report: dict[str, Any], failures: list[str]) -> None:
    environment = report.get("environment")
    if not isinstance(environment, dict):
        failures.append("Prime environment smoke report environment must be an object.")
        return
    if environment.get("environment_dir") != ENVIRONMENT_DIR.as_posix():
        failures.append("Prime environment smoke report environment_dir is incorrect.")
    if environment.get("entrypoint") != ENVIRONMENT_ENTRYPOINT:
        failures.append("Prime environment smoke report entrypoint is incorrect.")
    if environment.get("imports_without_verifiers") is not True:
        failures.append(
            "Prime environment smoke report requires Verifiers to import."
        )
    if environment.get("module_path") != ENVIRONMENT_MODULE_PATH.as_posix():
        failures.append("Prime environment smoke report module_path is incorrect.")


def _verify_dataset(report: dict[str, Any], failures: list[str]) -> None:
    dataset = report.get("dataset")
    if not isinstance(dataset, dict):
        failures.append("Prime environment smoke report dataset must be an object.")
        return
    for key in ("data_file_count", "dataset_rows"):
        if not isinstance(dataset.get(key), int):
            failures.append(f"Prime environment smoke report {key} is invalid.")
    if dataset.get("dataset_rows") != dataset.get("data_file_count"):
        failures.append("Prime environment smoke report data and rows diverge.")
    if dataset.get("default_attack_plan_id") != _DEFAULT_ATTACK_PLAN_ID:
        failures.append("Prime environment smoke report default AttackPlan is wrong.")
    families = dataset.get("families")
    if not isinstance(families, list) or not all(
        isinstance(family, str) for family in families
    ):
        failures.append("Prime environment smoke report families are invalid.")
    if dataset.get("mirrors_packaged_data") is not True:
        failures.append(
            "Prime environment smoke report does not mirror packaged data."
        )


def _verify_scoring(report: dict[str, Any], failures: list[str]) -> None:
    scoring = report.get("scoring")
    if not isinstance(scoring, dict):
        failures.append("Prime environment smoke report scoring must be an object.")
        return
    if scoring.get("accepted_score") != 1.0:
        failures.append("Prime environment smoke report accepted score is wrong.")
    if scoring.get("formal_artifact_binding_schema") != FORMAL_ARTIFACT_BINDING_SCHEMA:
        failures.append(
            "Prime environment smoke report formal artifact binding schema is wrong."
        )
    if (
        scoring.get("review_governance_binding_schema")
        != REVIEWER_GOVERNANCE_BINDING_SCHEMA
    ):
        failures.append(
            "Prime environment smoke report reviewer governance schema is wrong."
        )
    if scoring.get("review_governance_ok") is not True:
        failures.append(
            "Prime environment smoke report lacks reviewer governance."
        )
    if scoring.get("reviewer_quality") != 1.0:
        failures.append(
            "Prime environment smoke report reviewer quality is wrong."
        )
    rubric_terms = scoring.get("rubric_terms")
    accepted_rubric_scores = scoring.get("accepted_rubric_scores")
    if rubric_terms != [
        "accepted_attack_plan",
        "single_json_object",
        "formal_validity",
        "cryptographic_applicability",
        "no_security_overclaim",
        "student_readability",
        "reproducibility",
        "reviewer_quality",
        "task_match",
        "proof_obligation_coverage",
    ]:
        failures.append("Prime environment smoke report rubric terms are wrong.")
    if not isinstance(accepted_rubric_scores, dict) or set(
        accepted_rubric_scores
    ) != set(rubric_terms or []):
        failures.append(
            "Prime environment smoke report accepted rubric scores are invalid."
        )
    elif any(score != 1.0 for score in accepted_rubric_scores.values()):
        failures.append(
            "Prime environment smoke report accepted rubric scores are wrong."
        )
    for key in ("unsupported_score", "invalid_json_score", "prefixed_json_score"):
        if scoring.get(key) != 0.0:
            failures.append(f"Prime environment smoke report {key} is wrong.")
    if scoring.get("requires_single_json_object") is not True:
        failures.append(
            "Prime environment smoke report does not require single JSON."
        )


def _verify_optional_dependencies(
    report: dict[str, Any],
    failures: list[str],
) -> None:
    optional_dependencies = report.get("optional_dependencies")
    if not isinstance(optional_dependencies, dict):
        failures.append(
            "Prime environment smoke report optional_dependencies must be an object."
        )
        return
    if optional_dependencies.get("load_environment_boundary_ok") is not True:
        failures.append(
            "Prime environment smoke report optional dependency boundary failed."
        )
    if optional_dependencies.get("required_packages") != list(
        _REQUIRED_OPTIONAL_PACKAGES
    ):
        failures.append(
            "Prime environment smoke report required optional packages are wrong."
        )


def _verify_safety(report: dict[str, Any], failures: list[str]) -> None:
    safety = report.get("safety")
    if not isinstance(safety, dict):
        failures.append("Prime environment smoke report safety must be an object.")
        return
    for flag in _FALSE_SAFETY_FLAGS:
        if safety.get(flag) is not False:
            failures.append(f"Prime environment smoke report {flag} must be false.")


def _verify_release_gates(report: dict[str, Any], failures: list[str]) -> None:
    release_gates = report.get("release_gates")
    if not isinstance(release_gates, list):
        failures.append(
            "Prime environment smoke report release_gates must be a list."
        )
        return
    for gate in _RELEASE_GATES:
        if gate not in release_gates:
            failures.append(
                f"Prime environment smoke report release gate missing: {gate}"
            )


def _verification_summary(
    report: dict[str, Any],
    failures: list[str],
) -> dict[str, Any]:
    environment = (
        report.get("environment") if isinstance(report.get("environment"), dict) else {}
    )
    dataset = report.get("dataset") if isinstance(report.get("dataset"), dict) else {}
    scoring = report.get("scoring") if isinstance(report.get("scoring"), dict) else {}
    optional_dependencies = (
        report.get("optional_dependencies")
        if isinstance(report.get("optional_dependencies"), dict)
        else {}
    )
    return {
        "accepted_score": scoring.get("accepted_score"),
        "dataset_rows": dataset.get("dataset_rows"),
        "failure_count": len(failures),
        "formal_artifact_binding_schema": scoring.get(
            "formal_artifact_binding_schema"
        ),
        "imports_without_verifiers": environment.get("imports_without_verifiers"),
        "load_environment_boundary_ok": optional_dependencies.get(
            "load_environment_boundary_ok"
        ),
        "prefixed_json_score": scoring.get("prefixed_json_score"),
        "review_governance_ok": scoring.get("review_governance_ok"),
        "reviewer_quality": scoring.get("reviewer_quality"),
        "rubric_terms": len(scoring.get("rubric_terms", [])),
        "unsupported_score": scoring.get("unsupported_score"),
    }


def _assistant_completion(content: str) -> list[dict[str, str]]:
    return [{"role": "assistant", "content": content}]


def _info_for_attack_plan_id(
    rows: list[dict[str, Any]],
    attack_plan_id: str,
) -> dict[str, Any]:
    for row in rows:
        info = row.get("info")
        if isinstance(info, dict) and info.get("attack_plan_id") == attack_plan_id:
            return info
    raise ValueError(f"Prime environment task row is missing: {attack_plan_id}")


def _load_python_module(path: Path, module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _resolve_path(path: Path, *, root: Path | None) -> Path:
    if path.is_absolute() or root is None:
        return path
    return root / path


def _display_path(path: Path, *, root: Path) -> str:
    resolved = _resolve_path(path, root=root)
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError:
        return resolved.as_posix()


def _dict_or_empty(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}
