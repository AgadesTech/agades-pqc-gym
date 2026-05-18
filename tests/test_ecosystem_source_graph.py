from __future__ import annotations

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.ecosystem_source_graph import (
    ECOSYSTEM_SOURCE_GRAPH_SCHEMA,
    ECOSYSTEM_SOURCE_GRAPH_VERIFICATION_SCHEMA,
    build_ecosystem_source_graph,
    verify_ecosystem_source_graph,
    write_ecosystem_source_graph,
)


def test_ecosystem_source_graph_links_public_sources_contracts_and_families(
    tmp_path: Path,
) -> None:
    out = tmp_path / "ecosystem_source_graph.json"

    graph = write_ecosystem_source_graph(out)

    assert graph == build_ecosystem_source_graph()
    assert json.loads(out.read_text(encoding="utf-8")) == graph
    assert graph["schema_version"] == ECOSYSTEM_SOURCE_GRAPH_SCHEMA
    assert graph["project"] == {
        "name": "Agades PQC Gym",
        "package": "agades_pqc_gym",
        "repository": "https://github.com/AgadesTech/agades-pqc-gym",
    }
    assert graph["inputs"] == {
        "benchmark_source_contracts": "docs/benchmark_source_contracts.json",
        "family_support_matrix": "docs/family_support_matrix.json",
        "source_catalog": "docs/source_catalog.json",
    }
    assert graph["summary"] == {
        "benchmark_source_catalog_links": 18,
        "benchmark_source_contracts": 18,
        "family_count": 9,
        "family_cross_family_source_links": 27,
        "family_future_source_links": 21,
        "prime_source_ids": 8,
        "prime_visibility_anchor_ids": 3,
        "source_catalog_sources": 41,
        "unique_family_cross_family_source_ids": 3,
        "unique_family_future_source_ids": 15,
        "unresolved_benchmark_source_catalog_links": 0,
        "unresolved_family_source_links": 0,
    }
    assert graph["source_catalog"]["platform_counts"] == {
        "ebacs": 1,
        "github": 14,
        "hugging_face": 8,
        "nist": 7,
        "nvidia": 3,
        "prime_intellect": 8,
    }
    assert graph["prime_ecosystem"]["visibility_anchor_ids"] == [
        "prime-autonanogpt-speedrun",
        "prime-autonomous-speedrunning-experiments",
        "prime-quickstart",
    ]
    assert graph["safety"] == {
        "contains_private_traces": False,
        "current_public_verifier_uses_future_sources": False,
        "publishes_private_candidates": False,
        "security_claim": False,
    }


def test_committed_ecosystem_source_graph_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "ecosystem_source_graph.json"
    committed = Path("docs/ecosystem_source_graph.json")

    write_ecosystem_source_graph(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_ecosystem_source_graph_verify_accepts_committed_graph() -> None:
    result = verify_ecosystem_source_graph(Path("docs/ecosystem_source_graph.json"))

    assert result == {
        "schema_version": ECOSYSTEM_SOURCE_GRAPH_VERIFICATION_SCHEMA,
        "graph_path": "docs/ecosystem_source_graph.json",
        "accepted": True,
        "summary": {
            "benchmark_source_catalog_links": 18,
            "benchmark_source_contracts": 18,
            "failure_count": 0,
            "family_count": 9,
            "family_cross_family_source_links": 27,
            "family_future_source_links": 21,
            "prime_source_ids": 8,
            "prime_visibility_anchor_ids": 3,
            "source_catalog_sources": 41,
            "unique_family_cross_family_source_ids": 3,
            "unique_family_future_source_ids": 15,
            "unresolved_benchmark_source_catalog_links": 0,
            "unresolved_family_source_links": 0,
        },
        "failures": [],
    }


def test_ecosystem_source_graph_verify_rejects_missing_source_catalog_anchor(
    tmp_path: Path,
) -> None:
    copied_root = _copy_repo(tmp_path)
    catalog_path = copied_root / "docs" / "source_catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog["sources"] = [
        source
        for source in catalog["sources"]
        if source["id"] != "nist-hqc-selection"
    ]
    catalog_path.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n")
    graph_path = copied_root / "docs" / "ecosystem_source_graph.json"
    write_ecosystem_source_graph(graph_path, root=copied_root)

    result = verify_ecosystem_source_graph(graph_path, root=copied_root)

    assert result["accepted"] is False
    assert any(
        "nist-hqc-standardization-track" in failure
        and "nist-hqc-selection" in failure
        for failure in result["failures"]
    )


def test_ecosystem_source_graph_verify_rejects_family_source_without_contract(
    tmp_path: Path,
) -> None:
    copied_root = _copy_repo(tmp_path)
    matrix_path = copied_root / "docs" / "family_support_matrix.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    code_based = next(
        family for family in matrix["families"] if family["family"] == "CODE_BASED"
    )
    code_based["future_reviewed_adapter_source_ids"].append("unreviewed-source")
    code_based["future_reviewed_adapter_source_count"] = len(
        code_based["future_reviewed_adapter_source_ids"]
    )
    matrix_path.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n")
    graph_path = copied_root / "docs" / "ecosystem_source_graph.json"
    write_ecosystem_source_graph(graph_path, root=copied_root)

    result = verify_ecosystem_source_graph(graph_path, root=copied_root)

    assert result["accepted"] is False
    assert any(
        "CODE_BASED" in failure and "unreviewed-source" in failure
        for failure in result["failures"]
    )


def test_ecosystem_source_graph_verify_rejects_summary_drift(
    tmp_path: Path,
) -> None:
    graph = build_ecosystem_source_graph()
    graph["summary"] = {
        **graph["summary"],
        "family_future_source_links": 20,
    }
    out = tmp_path / "ecosystem_source_graph.json"
    out.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n")

    result = verify_ecosystem_source_graph(out)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 2
    assert result["failures"] == [
        "Ecosystem source graph is not in sync.",
        "manifest: summary is inconsistent with graph links.",
    ]


def test_ecosystem_source_graph_cli_writes_and_verifies_graph(
    tmp_path: Path,
) -> None:
    out = tmp_path / "ecosystem_source_graph.json"

    write_result = CliRunner().invoke(
        app,
        ["ecosystem-source-graph", "--out", str(out)],
    )

    assert write_result.exit_code == 0
    assert f"ecosystem_source_graph={out}" in write_result.output

    verify_result = CliRunner().invoke(
        app,
        ["ecosystem-source-graph-verify", "--graph", str(out)],
    )

    assert verify_result.exit_code == 0
    payload = json.loads(verify_result.output)
    assert payload["schema_version"] == ECOSYSTEM_SOURCE_GRAPH_VERIFICATION_SCHEMA
    assert payload["accepted"] is True


def _copy_repo(tmp_path: Path) -> Path:
    copied_root = tmp_path / "repo"
    shutil.copytree(
        Path.cwd(),
        copied_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".pytest_cache",
            ".ruff_cache",
            "build",
            "dist",
            "*.egg-info",
            "__pycache__",
        ),
    )
    return copied_root
