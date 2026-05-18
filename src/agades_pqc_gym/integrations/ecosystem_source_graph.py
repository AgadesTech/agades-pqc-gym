from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.integrations.benchmark_source_contracts import (
    verify_benchmark_source_contracts,
)
from agades_pqc_gym.integrations.family_support import verify_family_support_matrix
from agades_pqc_gym.integrations.source_catalog import verify_source_catalog

ECOSYSTEM_SOURCE_GRAPH_SCHEMA = "agades.pqc.ecosystem_source_graph.v1"
ECOSYSTEM_SOURCE_GRAPH_VERIFICATION_SCHEMA = (
    "agades.pqc.ecosystem_source_graph_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
PROJECT = {
    "name": "Agades PQC Gym",
    "package": "agades_pqc_gym",
    "repository": "https://github.com/AgadesTech/agades-pqc-gym",
}
SOURCE_CATALOG_PATH = Path("docs/source_catalog.json")
BENCHMARK_SOURCE_CONTRACTS_PATH = Path("docs/benchmark_source_contracts.json")
FAMILY_SUPPORT_MATRIX_PATH = Path("docs/family_support_matrix.json")
PRIME_VISIBILITY_ANCHOR_IDS = (
    "prime-autonanogpt-speedrun",
    "prime-autonomous-speedrunning-experiments",
    "prime-quickstart",
)
REQUIRED_RELEASE_GATES = [
    "uv run pytest tests/test_ecosystem_source_graph.py -q",
    "uv run agades-pqc ecosystem-source-graph --out "
    "docs/ecosystem_source_graph.json",
    "uv run agades-pqc ecosystem-source-graph-verify --graph "
    "docs/ecosystem_source_graph.json",
    "uv run agades-pqc source-catalog-verify --catalog docs/source_catalog.json",
    "uv run agades-pqc benchmark-source-verify --contracts "
    "docs/benchmark_source_contracts.json",
    "uv run agades-pqc family-support-verify --matrix "
    "docs/family_support_matrix.json",
]


def build_ecosystem_source_graph(root: Path | None = None) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    source_catalog = _read_json(project_root / SOURCE_CATALOG_PATH)
    source_catalog_sources = _dict_list(source_catalog.get("sources"))
    source_by_id = {
        source["id"]: source
        for source in source_catalog_sources
        if isinstance(source.get("id"), str)
    }

    benchmark_contracts = _read_json(project_root / BENCHMARK_SOURCE_CONTRACTS_PATH)
    contracts = _dict_list(benchmark_contracts.get("contracts"))
    contract_by_id = {
        contract["source_id"]: contract
        for contract in contracts
        if isinstance(contract.get("source_id"), str)
    }

    family_support = _read_json(project_root / FAMILY_SUPPORT_MATRIX_PATH)
    families = _dict_list(family_support.get("families"))

    benchmark_edges, unresolved_benchmark_links = _benchmark_source_catalog_edges(
        contracts,
        source_by_id,
    )
    family_edges, unresolved_family_links = _family_source_edges(
        families,
        contract_by_id,
        source_by_id,
    )
    future_source_ids = sorted(
        {
            edge["source_id"]
            for edge in family_edges
            if edge["relationship"] == "future_reviewed_adapter"
        }
    )
    cross_family_source_ids = sorted(
        {
            edge["source_id"]
            for edge in family_edges
            if edge["relationship"] == "cross_family_review_source"
        }
    )
    prime_source_ids = sorted(
        source_id
        for source_id, source in source_by_id.items()
        if source.get("platform") == "prime_intellect"
    )
    prime_visibility_anchor_ids = sorted(
        source_id
        for source_id in PRIME_VISIBILITY_ANCHOR_IDS
        if source_id in source_by_id
    )

    return {
        "schema_version": ECOSYSTEM_SOURCE_GRAPH_SCHEMA,
        "project": dict(PROJECT),
        "inputs": {
            "benchmark_source_contracts": BENCHMARK_SOURCE_CONTRACTS_PATH.as_posix(),
            "family_support_matrix": FAMILY_SUPPORT_MATRIX_PATH.as_posix(),
            "source_catalog": SOURCE_CATALOG_PATH.as_posix(),
        },
        "summary": {
            "benchmark_source_catalog_links": len(benchmark_edges),
            "benchmark_source_contracts": len(contracts),
            "family_count": len(families),
            "family_cross_family_source_links": sum(
                1
                for edge in family_edges
                if edge["relationship"] == "cross_family_review_source"
            ),
            "family_future_source_links": sum(
                1
                for edge in family_edges
                if edge["relationship"] == "future_reviewed_adapter"
            ),
            "prime_source_ids": len(prime_source_ids),
            "prime_visibility_anchor_ids": len(prime_visibility_anchor_ids),
            "source_catalog_sources": len(source_catalog_sources),
            "unique_family_cross_family_source_ids": len(cross_family_source_ids),
            "unique_family_future_source_ids": len(future_source_ids),
            "unresolved_benchmark_source_catalog_links": len(
                unresolved_benchmark_links
            ),
            "unresolved_family_source_links": len(unresolved_family_links),
        },
        "source_catalog": {
            "platform_counts": _platform_counts(source_catalog_sources),
            "source_ids": sorted(source_by_id),
        },
        "benchmark_source_catalog_edges": benchmark_edges,
        "family_source_edges": family_edges,
        "prime_ecosystem": {
            "source_ids": prime_source_ids,
            "visibility_anchor_ids": prime_visibility_anchor_ids,
        },
        "unresolved": {
            "benchmark_source_catalog_links": unresolved_benchmark_links,
            "family_source_links": unresolved_family_links,
        },
        "safety": {
            "contains_private_traces": False,
            "current_public_verifier_uses_future_sources": False,
            "publishes_private_candidates": False,
            "security_claim": False,
        },
        "release_gates": list(REQUIRED_RELEASE_GATES),
    }


def write_ecosystem_source_graph(
    out: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    graph = build_ecosystem_source_graph(root=root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(graph, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return graph


def verify_ecosystem_source_graph(
    graph_path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    graph = _read_graph(graph_path, failures)

    if graph.get("schema_version") != ECOSYSTEM_SOURCE_GRAPH_SCHEMA:
        failures.append(
            f"manifest: schema_version must be {ECOSYSTEM_SOURCE_GRAPH_SCHEMA}."
        )

    _verify_input_manifests(project_root, failures)

    expected = build_ecosystem_source_graph(root=project_root)
    if graph and graph != expected:
        failures.append("Ecosystem source graph is not in sync.")

    _verify_safety(graph, failures)
    _verify_unresolved_links(graph, failures)

    summary = _verification_summary(graph)
    if graph.get("summary") != summary:
        failures.append("manifest: summary is inconsistent with graph links.")
    summary["failure_count"] = len(failures)
    return {
        "schema_version": ECOSYSTEM_SOURCE_GRAPH_VERIFICATION_SCHEMA,
        "graph_path": str(graph_path),
        "accepted": not failures,
        "summary": summary,
        "failures": failures,
    }


def _read_graph(path: Path, failures: list[str]) -> dict[str, Any]:
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


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _text(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _benchmark_source_catalog_edges(
    contracts: list[dict[str, Any]],
    source_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    edges: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for contract in sorted(contracts, key=lambda item: str(item.get("source_id", ""))):
        source_id = _text(contract.get("source_id"))
        source_catalog_id = _text(contract.get("source_catalog_id"))
        if source_id is None or source_catalog_id is None:
            continue
        source = source_by_id.get(source_catalog_id)
        if source is None:
            unresolved.append(
                {
                    "source_id": source_id,
                    "source_catalog_id": source_catalog_id,
                }
            )
        edges.append(
            {
                "source_id": source_id,
                "source_catalog_id": source_catalog_id,
                "source_catalog_integration_status": (
                    source.get("integration_status") if source else None
                ),
                "source_catalog_platform": source.get("platform") if source else None,
                "target_family": contract.get("target_family"),
            }
        )
    return edges, unresolved


def _family_source_edges(
    families: list[dict[str, Any]],
    contract_by_id: dict[str, dict[str, Any]],
    source_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    edges: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for family in sorted(families, key=lambda item: str(item.get("family", ""))):
        family_id = _text(family.get("family"))
        if family_id is None:
            continue
        for field, relationship in (
            ("future_reviewed_adapter_source_ids", "future_reviewed_adapter"),
            ("cross_family_review_source_ids", "cross_family_review_source"),
        ):
            for source_id in _text_list(family.get(field)):
                contract = contract_by_id.get(source_id)
                source_catalog_id = (
                    _text(contract.get("source_catalog_id")) if contract else None
                )
                source = (
                    source_by_id.get(source_catalog_id)
                    if source_catalog_id is not None
                    else None
                )
                if contract is None:
                    unresolved.append(
                        {
                            "family": family_id,
                            "relationship": relationship,
                            "source_id": source_id,
                        }
                    )
                edges.append(
                    {
                        "family": family_id,
                        "relationship": relationship,
                        "source_id": source_id,
                        "source_catalog_id": source_catalog_id,
                        "source_catalog_platform": (
                            source.get("platform") if source else None
                        ),
                        "target_family": (
                            contract.get("target_family") if contract else None
                        ),
                    }
                )
    return edges, unresolved


def _text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted(item for item in value if isinstance(item, str))


def _platform_counts(sources: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for source in sources:
        platform = source.get("platform")
        if isinstance(platform, str) and platform:
            counts[platform] = counts.get(platform, 0) + 1
    return dict(sorted(counts.items()))


def _verify_input_manifests(project_root: Path, failures: list[str]) -> None:
    source_result = verify_source_catalog(
        project_root / SOURCE_CATALOG_PATH,
        root=project_root,
    )
    failures.extend(
        f"source_catalog: {failure}" for failure in source_result["failures"]
    )

    contract_result = verify_benchmark_source_contracts(
        project_root / BENCHMARK_SOURCE_CONTRACTS_PATH,
    )
    failures.extend(
        "benchmark_source_contracts: " + failure
        for failure in contract_result["failures"]
    )

    family_result = verify_family_support_matrix(
        project_root / FAMILY_SUPPORT_MATRIX_PATH,
    )
    failures.extend(
        f"family_support_matrix: {failure}"
        for failure in family_result["failures"]
    )


def _verify_safety(graph: dict[str, Any], failures: list[str]) -> None:
    safety = graph.get("safety")
    if not isinstance(safety, dict):
        failures.append("manifest: safety must be an object.")
        return
    for field in (
        "contains_private_traces",
        "current_public_verifier_uses_future_sources",
        "publishes_private_candidates",
        "security_claim",
    ):
        if safety.get(field) is not False:
            failures.append(f"manifest: safety.{field} must be false.")


def _verify_unresolved_links(graph: dict[str, Any], failures: list[str]) -> None:
    unresolved = graph.get("unresolved")
    if not isinstance(unresolved, dict):
        failures.append("manifest: unresolved must be an object.")
        return
    for link in _dict_list(unresolved.get("benchmark_source_catalog_links")):
        failures.append(
            f"{link.get('source_id')}: source_catalog_id is not present in "
            f"{SOURCE_CATALOG_PATH.as_posix()}: {link.get('source_catalog_id')}."
        )
    for link in _dict_list(unresolved.get("family_source_links")):
        failures.append(
            f"{link.get('family')}: {link.get('relationship')} has no benchmark "
            f"source contract: {link.get('source_id')}."
        )


def _verification_summary(graph: dict[str, Any]) -> dict[str, Any]:
    source_catalog = graph.get("source_catalog")
    if not isinstance(source_catalog, dict):
        source_catalog = {}
    prime_ecosystem = graph.get("prime_ecosystem")
    if not isinstance(prime_ecosystem, dict):
        prime_ecosystem = {}
    unresolved = graph.get("unresolved")
    if not isinstance(unresolved, dict):
        unresolved = {}

    benchmark_edges = _dict_list(graph.get("benchmark_source_catalog_edges"))
    family_edges = _dict_list(graph.get("family_source_edges"))
    future_source_ids = {
        edge.get("source_id")
        for edge in family_edges
        if edge.get("relationship") == "future_reviewed_adapter"
        and isinstance(edge.get("source_id"), str)
    }
    cross_family_source_ids = {
        edge.get("source_id")
        for edge in family_edges
        if edge.get("relationship") == "cross_family_review_source"
        and isinstance(edge.get("source_id"), str)
    }
    families = {
        edge.get("family")
        for edge in family_edges
        if isinstance(edge.get("family"), str)
    }

    return {
        "benchmark_source_catalog_links": len(benchmark_edges),
        "benchmark_source_contracts": len(benchmark_edges),
        "family_count": len(families),
        "family_cross_family_source_links": sum(
            1
            for edge in family_edges
            if edge.get("relationship") == "cross_family_review_source"
        ),
        "family_future_source_links": sum(
            1
            for edge in family_edges
            if edge.get("relationship") == "future_reviewed_adapter"
        ),
        "prime_source_ids": len(_text_list(prime_ecosystem.get("source_ids"))),
        "prime_visibility_anchor_ids": len(
            _text_list(prime_ecosystem.get("visibility_anchor_ids"))
        ),
        "source_catalog_sources": len(_text_list(source_catalog.get("source_ids"))),
        "unique_family_cross_family_source_ids": len(cross_family_source_ids),
        "unique_family_future_source_ids": len(future_source_ids),
        "unresolved_benchmark_source_catalog_links": len(
            _dict_list(unresolved.get("benchmark_source_catalog_links"))
        ),
        "unresolved_family_source_links": len(
            _dict_list(unresolved.get("family_source_links"))
        ),
    }
