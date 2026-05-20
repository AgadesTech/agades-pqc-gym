from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.registry import default_family_registry
from agades_pqc_gym.core.target import TargetFamily, TargetSpec
from agades_pqc_gym.integrations.benchmark_source_contracts import (
    build_benchmark_source_contracts,
)

FAMILY_SUPPORT_SCHEMA = "agades.pqc.family_support.v1"
FAMILY_SUPPORT_VERIFICATION_SCHEMA = "agades.pqc.family_support_verification.v1"
ROOT = Path(__file__).resolve().parents[3]

_PLUGIN_BY_FAMILY = {
    TargetFamily.LWE: "lattice",
    TargetFamily.MLWE: "lattice",
    TargetFamily.NTRU: "lattice",
    TargetFamily.SIS: "lattice",
    TargetFamily.CODE_BASED: "code_based",
    TargetFamily.MULTIVARIATE: "multivariate",
    TargetFamily.HASH_BASED: "hash_based",
    TargetFamily.ISOGENY_HISTORICAL: "isogeny_historical",
    TargetFamily.IMPLEMENTATION_SECURITY: "implementation_security",
}
_SOURCE_CONTRACT_TARGET_BY_FAMILY = {
    TargetFamily.LWE: "lattice",
    TargetFamily.MLWE: "lattice",
    TargetFamily.NTRU: "lattice",
    TargetFamily.SIS: "lattice",
    TargetFamily.CODE_BASED: "code_based",
    TargetFamily.MULTIVARIATE: "multivariate",
    TargetFamily.HASH_BASED: "hash_based",
    TargetFamily.ISOGENY_HISTORICAL: "isogeny_historical",
    TargetFamily.IMPLEMENTATION_SECURITY: "implementation_security",
}
_EXPECTED_FALSE_SAFETY_FLAGS = (
    "lattice_estimator_is_universal_pqc_oracle",
    "unsupported_families_return_fake_estimates",
    "arbitrary_code_execution",
    "security_claim",
)
_IMPLEMENTED_FAMILIES = ("LWE", "MLWE")
_SCHEMA_ONLY_LATTICE_FAMILIES = ("NTRU", "SIS")
_TOY_EVALUATOR_FAMILIES = (
    "CODE_BASED",
    "HASH_BASED",
    "IMPLEMENTATION_SECURITY",
    "ISOGENY_HISTORICAL",
    "MULTIVARIATE",
)
_LATTICE_ESTIMATOR_FAMILIES = ("LWE", "MLWE")


def build_family_support_matrix(root: Path | None = None) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    registry = default_family_registry()
    example_paths = _attack_plan_examples_by_family(project_root)
    benchmark_paths = _benchmarks_by_family(project_root)
    future_source_ids = _future_reviewed_source_contracts_by_family()
    cross_family_source_ids = _cross_family_review_source_ids()
    families = []
    for family in TargetFamily:
        adapter = registry.get(family)
        support_level = str(adapter.support_level)
        families.append(
            {
                "family": family.value,
                "plugin": _PLUGIN_BY_FAMILY[family],
                "support_level": support_level,
                "evaluator_status": _evaluator_status(family, support_level),
                "default_estimator": _default_estimator(family, support_level),
                "optional_estimators": _optional_estimators(family, support_level),
                "operators": sorted(adapter.supported_operators()),
                "public_examples": example_paths.get(family.value, []),
                "public_example_count": len(example_paths.get(family.value, [])),
                "benchmarks": benchmark_paths.get(family.value, []),
                "benchmark_count": len(benchmark_paths.get(family.value, [])),
                "reproduction_status": _reproduction_status(family, support_level),
                "future_reviewed_adapter_source_ids": future_source_ids[family],
                "future_reviewed_adapter_source_count": len(
                    future_source_ids[family]
                ),
                "cross_family_review_source_ids": cross_family_source_ids,
                "cross_family_review_source_count": len(cross_family_source_ids),
                "review_required_before_claims": True,
            }
        )

    matrix = {
        "schema_version": FAMILY_SUPPORT_SCHEMA,
        "project": {
            "name": "Agades PQC Gym",
            "package": "agades_pqc_gym",
            "repository": "https://github.com/AgadesTech/agades-pqc-gym",
        },
        "families": families,
        "safety": {
            "lattice_estimator_is_universal_pqc_oracle": False,
            "unsupported_families_return_fake_estimates": False,
            "arbitrary_code_execution": False,
            "security_claim": False,
        },
        "release_gates": [
            "uv run pytest tests/test_family_support_matrix.py -q",
            "uv run agades-pqc family-support --out docs/family_support_matrix.json",
            "uv run agades-pqc family-support-verify --matrix "
            "docs/family_support_matrix.json",
        ],
    }
    matrix["summary"] = summarize_family_support_matrix(matrix)
    return matrix


def write_family_support_matrix(
    out: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    matrix = build_family_support_matrix(root=root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(matrix, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return matrix


def summarize_family_support_matrix(matrix: dict[str, Any]) -> dict[str, Any]:
    families = [
        family
        for family in matrix.get("families", [])
        if isinstance(family, dict) and isinstance(family.get("family"), str)
    ]
    plugins = sorted(
        {
            plugin
            for family in families
            if isinstance((plugin := family.get("plugin")), str)
        }
    )
    support_level_counts = {
        support_level: sum(
            1 for family in families if family.get("support_level") == support_level
        )
        for support_level in ("implemented", "schema_only", "toy_evaluator")
    }
    future_source_ids = sorted(
        {
            source_id
            for family in families
            for source_id in _list_or_empty(
                family.get("future_reviewed_adapter_source_ids")
            )
            if isinstance(source_id, str)
        }
    )
    cross_family_source_ids = sorted(
        {
            source_id
            for family in families
            for source_id in _list_or_empty(
                family.get("cross_family_review_source_ids")
            )
            if isinstance(source_id, str)
        }
    )
    return {
        "benchmark_count": sum(
            len(_list_or_empty(family.get("benchmarks"))) for family in families
        ),
        "cross_family_review_source_count": len(cross_family_source_ids),
        "family_count": len(families),
        "implemented": _families_by_support_level(families, "implemented"),
        "schema_only": _families_by_support_level(families, "schema_only"),
        "toy_evaluators": _families_by_support_level(families, "toy_evaluator"),
        "families_with_future_reviewed_adapters": sorted(
            family["family"]
            for family in families
            if _list_or_empty(family.get("future_reviewed_adapter_source_ids"))
        ),
        "per_family_future_reviewed_adapter_source_counts": {
            family["family"]: len(
                _list_or_empty(family.get("future_reviewed_adapter_source_ids"))
            )
            for family in sorted(families, key=lambda item: item["family"])
        },
        "plugin_count": len(plugins),
        "plugins": plugins,
        "public_example_count": sum(
            len(_list_or_empty(family.get("public_examples"))) for family in families
        ),
        "review_required_before_claims": bool(families)
        and all(
            family.get("review_required_before_claims") is True
            for family in families
        ),
        "support_level_counts": support_level_counts,
        "unique_future_reviewed_adapter_source_count": len(future_source_ids),
    }


def summarize_family_support_publication_gate(
    family_support: dict[str, Any],
    platform_family_supports: dict[str, dict[str, Any]],
    *,
    required_platforms: tuple[str, ...],
) -> dict[str, Any]:
    platforms = sorted(platform_family_supports)
    platforms_with_claim_review_gate = sorted(
        platform
        for platform, support in platform_family_supports.items()
        if support.get("review_required_before_claims") is True
    )
    missing_claim_review_gate = sorted(
        platform
        for platform in required_platforms
        if platform not in platforms_with_claim_review_gate
    )
    future_source_counts = _dict_or_empty(
        family_support.get("per_family_future_reviewed_adapter_source_counts")
    )

    return {
        "family_count": family_support.get("family_count"),
        "implemented": _list_or_empty(family_support.get("implemented")),
        "schema_only": _list_or_empty(family_support.get("schema_only")),
        "toy_evaluators": _list_or_empty(family_support.get("toy_evaluators")),
        "families_with_future_reviewed_adapters": _list_or_empty(
            family_support.get("families_with_future_reviewed_adapters")
        ),
        "future_reviewed_adapter_sources_by_family": _int_value_sum(
            future_source_counts
        ),
        "unique_future_reviewed_adapter_source_count": family_support.get(
            "unique_future_reviewed_adapter_source_count"
        ),
        "review_required_before_claims": family_support.get(
            "review_required_before_claims"
        ),
        "platform_support": {
            "family_counts_match": _platform_family_counts_match(
                platform_family_supports,
                family_support.get("family_count"),
                required_platforms=required_platforms,
            ),
            "missing_claim_review_gate": missing_claim_review_gate,
            "platforms": platforms,
            "platforms_with_claim_review_gate": platforms_with_claim_review_gate,
            "surface_count": len(platform_family_supports),
        },
    }


def build_family_readiness_matrix(
    family_support_matrix: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    families = [
        family
        for family in family_support_matrix.get("families", [])
        if isinstance(family, dict) and isinstance(family.get("family"), str)
    ]
    readiness: dict[str, dict[str, Any]] = {}
    for family in sorted(families, key=lambda item: item["family"]):
        optional_estimators = _list_or_empty(family.get("optional_estimators"))
        readiness[family["family"]] = {
            "benchmark_count": family.get("benchmark_count"),
            "cross_family_review_source_count": family.get(
                "cross_family_review_source_count"
            ),
            "default_estimator": family.get("default_estimator"),
            "evaluator_status": family.get("evaluator_status"),
            "future_reviewed_adapter_source_count": family.get(
                "future_reviewed_adapter_source_count"
            ),
            "lattice_estimator_enabled": "lattice-estimator"
            in optional_estimators,
            "operator_count": len(_list_or_empty(family.get("operators"))),
            "plugin": family.get("plugin"),
            "public_example_count": family.get("public_example_count"),
            "reproduction_status": family.get("reproduction_status"),
            "review_required_before_claims": family.get(
                "review_required_before_claims"
            ),
            "support_level": family.get("support_level"),
        }
    return readiness


def summarize_family_readiness_matrix(matrix: dict[str, Any]) -> dict[str, Any]:
    entries = {
        family: readiness
        for family, readiness in matrix.items()
        if isinstance(family, str) and isinstance(readiness, dict)
    }
    lattice_estimator_families = sorted(
        family
        for family, readiness in entries.items()
        if readiness.get("lattice_estimator_enabled") is True
    )
    non_lattice_lattice_estimator_families = sorted(
        family
        for family in lattice_estimator_families
        if family not in _LATTICE_ESTIMATOR_FAMILIES
    )
    schema_only_default_estimator_families = sorted(
        family
        for family, readiness in entries.items()
        if readiness.get("support_level") == "schema_only"
        and readiness.get("default_estimator") is not None
    )
    return {
        "family_count": len(entries),
        "lattice_estimator_families": lattice_estimator_families,
        "non_lattice_lattice_estimator_families": (
            non_lattice_lattice_estimator_families
        ),
        "review_required_families": sum(
            1
            for readiness in entries.values()
            if readiness.get("review_required_before_claims") is True
        ),
        "schema_only_default_estimator_families": (
            schema_only_default_estimator_families
        ),
    }


def verify_family_support_matrix(
    path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    failures: list[str] = []
    matrix = _read_family_support_matrix(path, failures)
    project_root = (root or ROOT).resolve()

    if matrix.get("schema_version") != FAMILY_SUPPORT_SCHEMA:
        failures.append(
            f"manifest: schema_version must be {FAMILY_SUPPORT_SCHEMA}."
        )

    _verify_safety(matrix, failures)

    families = matrix.get("families")
    if not isinstance(families, list):
        failures.append("manifest: families must be a list.")
        families = []

    entry_failure_count = len(failures)
    summary = _verify_family_entries(families, failures)
    stored_summary = matrix.get("summary")
    expected_summary = {
        key: value for key, value in summary.items() if key != "failure_count"
    }
    if len(failures) == entry_failure_count and stored_summary != expected_summary:
        failures.append("manifest: summary is inconsistent with family entries.")
    if not failures and matrix != build_family_support_matrix(root=project_root):
        failures.append(
            "manifest: contents are not synchronized with the current runtime "
            "family support matrix."
        )
    summary["failure_count"] = len(failures)

    return {
        "schema_version": FAMILY_SUPPORT_VERIFICATION_SCHEMA,
        "matrix_path": str(path),
        "accepted": not failures,
        "summary": summary,
        "failures": failures,
    }


def _read_family_support_matrix(path: Path, failures: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"manifest: missing file {path}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(f"manifest: invalid JSON at line {exc.lineno}.")
        return {}

    if not isinstance(payload, dict):
        failures.append("manifest: top-level JSON value must be an object.")
        return {}
    return payload


def _verify_safety(matrix: dict[str, Any], failures: list[str]) -> None:
    safety = matrix.get("safety")
    if not isinstance(safety, dict):
        failures.append("manifest: safety must be an object.")
        return

    for flag in _EXPECTED_FALSE_SAFETY_FLAGS:
        if safety.get(flag) is not False:
            failures.append(f"manifest: safety.{flag} must be false.")


def _verify_family_entries(
    families: list[Any],
    failures: list[str],
) -> dict[str, Any]:
    by_family: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(families):
        if not isinstance(entry, dict):
            failures.append(f"family[{index}]: family entry must be an object.")
            continue
        family = entry.get("family")
        if not isinstance(family, str) or not family:
            failures.append(f"family[{index}]: family must be a non-empty string.")
            continue
        if family in by_family:
            failures.append(f"{family}: duplicate family support entry.")
            continue
        by_family[family] = entry

    expected_families = {family.value for family in TargetFamily}
    observed_families = set(by_family)
    for missing in sorted(expected_families - observed_families):
        failures.append(f"{missing}: missing family support entry.")
    for unexpected in sorted(observed_families - expected_families):
        failures.append(f"{unexpected}: unexpected family support entry.")

    for family, entry in by_family.items():
        _verify_family_entry(entry, family, failures)

    return summarize_family_support_matrix({"families": list(by_family.values())})


def _verify_family_entry(
    entry: dict[str, Any],
    family: str,
    failures: list[str],
) -> None:
    try:
        target_family = TargetFamily(family)
    except ValueError:
        failures.append(f"{family}: unexpected family support entry.")
        return

    expected_plugin = _PLUGIN_BY_FAMILY[target_family]
    if entry.get("plugin") != expected_plugin:
        failures.append(f"{family}: plugin must be {expected_plugin}.")

    support_level = entry.get("support_level")
    if family in _IMPLEMENTED_FAMILIES:
        if support_level != "implemented":
            failures.append(f"{family}: LWE and MLWE must remain implemented.")
    elif family in _SCHEMA_ONLY_LATTICE_FAMILIES:
        if support_level != "schema_only":
            failures.append(
                f"{family}: NTRU and SIS must remain schema_only until reviewed."
            )
    elif support_level == "implemented":
        failures.append(
            f"{family}: non-lattice families must not be marked implemented."
        )
    elif support_level != "toy_evaluator":
        failures.append(f"{family}: non-lattice families must remain toy_evaluator.")

    for field in ("operators", "public_examples", "benchmarks"):
        if not _is_text_list(entry.get(field)):
            failures.append(f"{family}: {field} must be a string list.")
    for field in (
        "future_reviewed_adapter_source_ids",
        "cross_family_review_source_ids",
    ):
        if not _is_text_list(entry.get(field)):
            failures.append(f"{family}: {field} must be a string list.")

    public_examples = entry.get("public_examples")
    if isinstance(public_examples, list) and (
        entry.get("public_example_count") != len(public_examples)
    ):
        failures.append(f"{family}: public_example_count is inconsistent.")

    benchmarks = entry.get("benchmarks")
    if isinstance(benchmarks, list) and entry.get("benchmark_count") != len(benchmarks):
        failures.append(f"{family}: benchmark_count is inconsistent.")

    if entry.get("review_required_before_claims") is not True:
        failures.append(f"{family}: review_required_before_claims must be true.")

    expected_future_source_ids = _future_reviewed_source_contracts_by_family()[
        target_family
    ]
    if entry.get("future_reviewed_adapter_source_ids") != expected_future_source_ids:
        failures.append(f"{family}: future_reviewed_adapter_source_ids drifted.")
    if entry.get("future_reviewed_adapter_source_count") != len(
        expected_future_source_ids
    ):
        failures.append(f"{family}: future_reviewed_adapter_source_count drifted.")

    expected_cross_family_source_ids = _cross_family_review_source_ids()
    if entry.get("cross_family_review_source_ids") != expected_cross_family_source_ids:
        failures.append(f"{family}: cross_family_review_source_ids drifted.")
    if entry.get("cross_family_review_source_count") != len(
        expected_cross_family_source_ids
    ):
        failures.append(f"{family}: cross_family_review_source_count drifted.")

    if support_level == "toy_evaluator":
        _verify_toy_family_entry(entry, family, failures)
    if support_level == "schema_only" and entry.get("default_estimator") is not None:
        failures.append(f"{family}: schema-only families must not name an estimator.")


def _verify_toy_family_entry(
    entry: dict[str, Any],
    family: str,
    failures: list[str],
) -> None:
    if family not in _TOY_EVALUATOR_FAMILIES:
        failures.append(f"{family}: unexpected toy evaluator family.")
    if entry.get("evaluator_status") != "implemented_toy":
        failures.append(f"{family}: toy evaluators must use implemented_toy status.")
    if not isinstance(entry.get("default_estimator"), str):
        failures.append(f"{family}: toy evaluators must name a default estimator.")
    if not entry.get("operators"):
        failures.append(f"{family}: toy evaluators must list operators.")
    if not entry.get("public_examples"):
        failures.append(f"{family}: toy evaluators must list public examples.")
    if not entry.get("benchmarks"):
        failures.append(f"{family}: toy evaluators must list benchmarks.")
    if entry.get("reproduction_status") == "not_implemented":
        failures.append(f"{family}: toy evaluators must describe reproduction status.")


def _is_text_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _platform_family_counts_match(
    platform_family_supports: dict[str, dict[str, Any]],
    root_family_count: Any,
    *,
    required_platforms: tuple[str, ...],
) -> bool:
    if set(platform_family_supports) != set(required_platforms):
        return False
    return all(
        support.get("family_count") == root_family_count
        for support in platform_family_supports.values()
    )


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_or_empty(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _int_value_sum(value: dict[str, Any]) -> int:
    total = 0
    for item in value.values():
        if isinstance(item, int):
            total += item
    return total


def _families_by_support_level(
    families: list[dict[str, Any]],
    support_level: str,
) -> list[str]:
    return sorted(
        family["family"]
        for family in families
        if family.get("support_level") == support_level
    )


def _future_reviewed_source_contracts_by_family() -> dict[TargetFamily, list[str]]:
    contracts = build_benchmark_source_contracts()["contracts"]
    source_ids_by_target: dict[str, list[str]] = {}
    for contract in contracts:
        target_family = contract["target_family"]
        if target_family == "all":
            continue
        source_ids_by_target.setdefault(target_family, []).append(contract["source_id"])

    return {
        family: sorted(
            source_ids_by_target.get(_SOURCE_CONTRACT_TARGET_BY_FAMILY[family], [])
        )
        for family in TargetFamily
    }


def _cross_family_review_source_ids() -> list[str]:
    return sorted(
        contract["source_id"]
        for contract in build_benchmark_source_contracts()["contracts"]
        if contract["target_family"] == "all"
    )


def _attack_plan_examples_by_family(root: Path) -> dict[str, list[str]]:
    examples: dict[str, list[str]] = {}
    for path in sorted((root / "examples" / "attack_plans").glob("*.json")):
        if path.name.startswith("invalid_"):
            continue
        try:
            plan = AttackPlan.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValidationError):
            continue
        if not plan.metadata.public:
            continue
        examples.setdefault(plan.target.family.value, []).append(
            str(path.relative_to(root))
        )
    return examples


def _benchmarks_by_family(root: Path) -> dict[str, list[str]]:
    benchmarks: dict[str, list[str]] = {}
    for path in sorted((root / "benchmarks").glob("*/*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            target = TargetSpec.model_validate(data.get("target", data))
        except (OSError, ValidationError, json.JSONDecodeError):
            continue
        benchmarks.setdefault(target.family.value, []).append(
            str(path.relative_to(root))
        )
    return benchmarks


def _evaluator_status(family: TargetFamily, support_level: str) -> str:
    if _implemented_lattice_family(family, support_level):
        return "implemented"
    if family is TargetFamily.CODE_BASED and support_level == "toy_evaluator":
        return "implemented_toy"
    if family is TargetFamily.MULTIVARIATE and support_level == "toy_evaluator":
        return "implemented_toy"
    if family is TargetFamily.HASH_BASED and support_level == "toy_evaluator":
        return "implemented_toy"
    if (
        family is TargetFamily.ISOGENY_HISTORICAL
        and support_level == "toy_evaluator"
    ):
        return "implemented_toy"
    if (
        family is TargetFamily.IMPLEMENTATION_SECURITY
        and support_level == "toy_evaluator"
    ):
        return "implemented_toy"
    if family in {TargetFamily.NTRU, TargetFamily.SIS}:
        return "unsupported_until_review"
    return "unsupported_schema_only"


def _default_estimator(family: TargetFamily, support_level: str) -> str | None:
    if _implemented_lattice_family(family, support_level):
        return "mock-lattice-estimator"
    if family is TargetFamily.CODE_BASED and support_level == "toy_evaluator":
        return "toy-code-based-isd-estimator"
    if family is TargetFamily.MULTIVARIATE and support_level == "toy_evaluator":
        return "toy-multivariate-estimator"
    if family is TargetFamily.HASH_BASED and support_level == "toy_evaluator":
        return "toy-hash-bound-estimator"
    if (
        family is TargetFamily.ISOGENY_HISTORICAL
        and support_level == "toy_evaluator"
    ):
        return "toy-isogeny-historical-path-estimator"
    if (
        family is TargetFamily.IMPLEMENTATION_SECURITY
        and support_level == "toy_evaluator"
    ):
        return "toy-implementation-security-estimator"
    return None


def _optional_estimators(family: TargetFamily, support_level: str) -> list[str]:
    if _implemented_lattice_family(family, support_level):
        return ["lattice-estimator"]
    if family is TargetFamily.CODE_BASED and support_level == "toy_evaluator":
        return [
            "toy-code-based-bit-flip-decoder-estimator",
            "toy-code-based-classic-mceliece-support-syndrome-estimator",
            "toy-code-based-classic-mceliece-syndrome-estimator",
            "toy-code-based-circulant-erasure-decoder-estimator",
            "toy-code-based-circulant-syndrome-decoder-estimator",
            "toy-code-based-erasure-syndrome-decoder-estimator",
            "toy-code-based-parity-check-decoder-estimator",
            "toy-code-based-repetition-decoder-estimator",
            "toy-code-based-weighted-repetition-decoder-estimator",
        ]
    return []


def _reproduction_status(family: TargetFamily, support_level: str) -> str:
    if _implemented_lattice_family(family, support_level):
        return (
            "downscaled_lwe_mlwe_fixture_solvers_and_estimator_replay_available_"
            "for_public_toy_targets"
        )
    if family is TargetFamily.CODE_BASED and support_level == "toy_evaluator":
        return (
            "toy_syndrome_hqc_mdpc_and_classic_mceliece_fixture_solvers_"
            "available_for_public_fixtures"
        )
    if family is TargetFamily.MULTIVARIATE and support_level == "toy_evaluator":
        return "toy_mq_and_minrank_solvers_available_for_public_gf2_fixtures"
    if family is TargetFamily.HASH_BASED and support_level == "toy_evaluator":
        return (
            "toy_preimage_collision_signature_merkle_fors_slh_dsa_and_misuse_verifiers_"
            "available_for_public_fixtures"
        )
    if (
        family is TargetFamily.ISOGENY_HISTORICAL
        and support_level == "toy_evaluator"
    ):
        return "historical_toy_path_verifier_available_for_public_fixtures"
    if (
        family is TargetFamily.IMPLEMENTATION_SECURITY
        and support_level == "toy_evaluator"
    ):
        return (
            "toy_kat_acvp_timing_and_benchmark_verifiers_available_for_public_"
            "json_only_fixtures"
        )
    return "not_implemented"


def _implemented_lattice_family(family: TargetFamily, support_level: str) -> bool:
    return family in {TargetFamily.LWE, TargetFamily.MLWE} and (
        support_level == "implemented"
    )
