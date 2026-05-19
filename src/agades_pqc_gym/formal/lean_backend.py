from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

from agades_pqc_gym.formal.artifacts import BACKEND
from agades_pqc_gym.utils.hashing import stable_sha256

FORMAL_LEAN_BACKEND_SCHEMA = "agades.pqc.formal.lean_backend.v1"
FORMAL_LEAN_BACKEND_VERIFICATION_SCHEMA = (
    "agades.pqc.formal.lean_backend_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BACKEND_PATH = Path("docs/formal_lean_backend.json")
DEFAULT_WORKFLOW_PATH = Path(".github/workflows/ci.yml")
LEAN_ROOT = Path("formal/lean")
LEAN_PROJECT = {
    "root": "formal/lean",
    "toolchain": "formal/lean/lean-toolchain",
    "lakefile": "formal/lean/lakefile.lean",
    "entry_module": "formal/lean/AgadesPQC.lean",
    "build_command": "lake build",
}
CI_GATE = {
    "workflow_path": ".github/workflows/ci.yml",
    "job": "test",
    "step_name": "Build Lean formal backend",
    "uses": "leanprover/lean-action@v1",
    "lake_package_directory": "formal/lean",
    "build": True,
    "test": False,
    "lint": False,
}
CI_STEP_WITH = {
    "lake-package-directory": "formal/lean",
    "build": True,
    "test": False,
    "lint": False,
    "auto-config": False,
    "use-mathlib-cache": True,
}
PLACEHOLDER_PATTERNS = {
    "contains_sorry": re.compile(r"\bsorry\b"),
    "contains_admit": re.compile(r"\badmit\b"),
    "contains_axiom": re.compile(r"\baxiom\b"),
}


def build_formal_lean_backend(
    *,
    root: Path | None = None,
    workflow_path: Path = DEFAULT_WORKFLOW_PATH,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    sources = _lean_sources(project_root)
    placeholder_scan = _placeholder_scan(sources)
    ci = _ci_gate(project_root, workflow_path)
    manifest = {
        "schema_version": FORMAL_LEAN_BACKEND_SCHEMA,
        "project": {
            "name": "Agades PQC Gym",
            "repository": "https://github.com/AgadesTech/agades-pqc-gym",
            "package": "agades_pqc_gym",
        },
        "backend": dict(BACKEND),
        "lean_project": {
            **LEAN_PROJECT,
            "toolchain_value": _toolchain_value(project_root),
        },
        "ci": ci,
        "placeholder_scan": placeholder_scan,
        "lean_sources": sources,
        "summary": _summary(sources, ci, placeholder_scan),
        "release_gates": [
            "uv run pytest tests/test_formal_lean_backend.py -q",
            "uv run agades-pqc formal-lean-backend --out "
            "docs/formal_lean_backend.json",
            "uv run agades-pqc formal-lean-backend-verify --backend "
            "docs/formal_lean_backend.json",
            "GitHub CI: Build Lean formal backend via leanprover/lean-action@v1",
        ],
    }
    manifest["manifest_sha256"] = _manifest_sha256(manifest)
    return manifest


def write_formal_lean_backend(
    out: Path = DEFAULT_BACKEND_PATH,
    *,
    root: Path | None = None,
    workflow_path: Path = DEFAULT_WORKFLOW_PATH,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    manifest = build_formal_lean_backend(
        root=project_root,
        workflow_path=workflow_path,
    )
    resolved = _resolve_path(out, project_root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def verify_formal_lean_backend(
    backend_path: Path = DEFAULT_BACKEND_PATH,
    *,
    root: Path | None = None,
    workflow_path: Path = DEFAULT_WORKFLOW_PATH,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    manifest = _read_json_object(
        _resolve_path(backend_path, project_root),
        "Formal Lean backend",
        failures,
    )
    expected = build_formal_lean_backend(
        root=project_root,
        workflow_path=workflow_path,
    )
    if manifest and manifest != expected:
        failures.append("Formal Lean backend manifest is not in sync.")
    if manifest:
        _verify_shape(manifest, project_root, failures)
        _verify_hash(manifest, failures)
        _verify_sources(manifest, project_root, failures)
        _verify_ci_gate(manifest, project_root, workflow_path, failures)

    summary = {
        "source_modules": len(manifest.get("lean_sources", [])),
        "theorem_declarations": sum(
            len(source.get("theorems", []))
            for source in _list_or_empty(manifest.get("lean_sources"))
            if isinstance(source, dict)
        ),
        "ci_lean_build_gate": bool(
            manifest.get("summary", {}).get("ci_lean_build_gate")
        ),
        "placeholder_failures": int(
            manifest.get("summary", {}).get("placeholder_failures", 0)
        ),
        "failure_count": len(failures),
    }
    return {
        "schema_version": FORMAL_LEAN_BACKEND_VERIFICATION_SCHEMA,
        "backend_path": backend_path.as_posix(),
        "accepted": not failures,
        "summary": summary,
        "failures": failures,
    }


def _lean_sources(root: Path) -> list[dict[str, Any]]:
    source_paths = sorted(
        path
        for path in (root / LEAN_ROOT).rglob("*.lean")
        if path.name != "lakefile.lean"
    )
    sources: list[dict[str, Any]] = []
    for path in source_paths:
        text = path.read_text(encoding="utf-8")
        rel_path = path.relative_to(root).as_posix()
        sources.append(
            {
                "path": rel_path,
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "theorems": _theorem_names(text),
                "imports": _imports(text),
                "placeholder_scan": _placeholder_scan_for_text(text),
            }
        )
    return sources


def _theorem_names(text: str) -> list[str]:
    namespace_stack: list[str] = []
    theorem_names: list[str] = []
    for line in text.splitlines():
        namespace_match = re.match(r"^\s*namespace\s+([A-Za-z0-9_'.]+)\s*$", line)
        if namespace_match:
            namespace_stack.append(namespace_match.group(1))
            continue
        end_match = re.match(r"^\s*end(?:\s+([A-Za-z0-9_'.]+))?\s*$", line)
        if end_match and namespace_stack:
            namespace_stack.pop()
            continue
        theorem_match = re.match(r"^\s*theorem\s+([A-Za-z0-9_'.]+)\b", line)
        if theorem_match:
            theorem_name = theorem_match.group(1)
            theorem_names.append(".".join([*namespace_stack, theorem_name]))
    return theorem_names


def _imports(text: str) -> list[str]:
    imports: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^\s*import\s+(.+?)\s*$", line)
        if match:
            imports.append(match.group(1))
    return imports


def _placeholder_scan(sources: list[dict[str, Any]]) -> dict[str, bool]:
    return {
        key: any(
            source.get("placeholder_scan", {}).get(key) is True
            for source in sources
        )
        for key in PLACEHOLDER_PATTERNS
    }


def _placeholder_scan_for_text(text: str) -> dict[str, bool]:
    return {
        key: bool(pattern.search(text))
        for key, pattern in PLACEHOLDER_PATTERNS.items()
    }


def _ci_gate(root: Path, workflow_path: Path) -> dict[str, Any]:
    workflow_rel = workflow_path.as_posix()
    workflow_abs = _resolve_path(workflow_path, root)
    try:
        workflow = yaml.safe_load(workflow_abs.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {**CI_GATE, "workflow_path": workflow_rel, "present": False}
    if not isinstance(workflow, dict):
        return {**CI_GATE, "workflow_path": workflow_rel, "present": False}
    steps = (
        workflow.get("jobs", {})
        .get(CI_GATE["job"], {})
        .get("steps", [])
    )
    for step in steps if isinstance(steps, list) else []:
        if not isinstance(step, dict):
            continue
        if step.get("name") != CI_GATE["step_name"]:
            continue
        raw_with_config = step.get("with", {})
        with_config = raw_with_config if isinstance(raw_with_config, dict) else {}
        return {
            "workflow_path": workflow_rel,
            "job": CI_GATE["job"],
            "step_name": CI_GATE["step_name"],
            "uses": step.get("uses"),
            "lake_package_directory": with_config.get("lake-package-directory"),
            "build": with_config.get("build"),
            "test": with_config.get("test"),
            "lint": with_config.get("lint"),
        }
    return {**CI_GATE, "workflow_path": workflow_rel, "present": False}


def _toolchain_value(root: Path) -> str:
    return (root / LEAN_PROJECT["toolchain"]).read_text(encoding="utf-8").strip()


def _summary(
    sources: list[dict[str, Any]],
    ci: dict[str, Any],
    placeholder_scan: dict[str, bool],
) -> dict[str, Any]:
    return {
        "source_modules": len(sources),
        "theorem_declarations": sum(len(source["theorems"]) for source in sources),
        "ci_lean_build_gate": _ci_gate_matches(ci),
        "placeholder_failures": sum(1 for found in placeholder_scan.values() if found),
    }


def _verify_shape(
    manifest: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    if manifest.get("schema_version") != FORMAL_LEAN_BACKEND_SCHEMA:
        failures.append(
            "Formal Lean backend schema_version must be "
            f"{FORMAL_LEAN_BACKEND_SCHEMA}."
        )
    if manifest.get("backend") != BACKEND:
        failures.append("Formal Lean backend must use Lean 4 + Mathlib.")
    lean_project = _dict_or_empty(manifest.get("lean_project"))
    expected_project = {
        **LEAN_PROJECT,
        "toolchain_value": _toolchain_value(root),
    }
    if lean_project != expected_project:
        failures.append("Formal Lean backend project binding is incorrect.")
    placeholder_scan = _dict_or_empty(manifest.get("placeholder_scan"))
    if any(placeholder_scan.get(key) is not False for key in PLACEHOLDER_PATTERNS):
        failures.append("Formal Lean backend contains proof placeholders.")
    sources = [
        source
        for source in _list_or_empty(manifest.get("lean_sources"))
        if isinstance(source, dict)
    ]
    if manifest.get("summary") != _summary(
        sources,
        _dict_or_empty(manifest.get("ci")),
        placeholder_scan,
    ):
        failures.append("Formal Lean backend summary is inconsistent.")


def _verify_hash(manifest: dict[str, Any], failures: list[str]) -> None:
    if manifest.get("manifest_sha256") != _manifest_sha256(manifest):
        failures.append("Formal Lean backend manifest hash does not match.")


def _verify_sources(
    manifest: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    expected_sources = _lean_sources(root)
    if manifest.get("lean_sources") != expected_sources:
        failures.append("Formal Lean backend source bindings are not in sync.")
    for source in _list_or_empty(manifest.get("lean_sources")):
        if not isinstance(source, dict):
            failures.append("Formal Lean source entry must be an object.")
            continue
        path_value = source.get("path")
        if not isinstance(path_value, str):
            failures.append("Formal Lean source path is missing.")
            continue
        path = root / path_value
        try:
            raw = path.read_bytes()
        except FileNotFoundError:
            failures.append(f"Formal Lean source is missing: {path_value}.")
            continue
        if source.get("sha256") != hashlib.sha256(raw).hexdigest():
            failures.append(f"Formal Lean source hash mismatch: {path_value}.")
        if any(
            source.get("placeholder_scan", {}).get(key) is True
            for key in PLACEHOLDER_PATTERNS
        ):
            failures.append(f"Formal Lean source contains placeholder: {path_value}.")


def _verify_ci_gate(
    manifest: dict[str, Any],
    root: Path,
    workflow_path: Path,
    failures: list[str],
) -> None:
    expected = _ci_gate(root, workflow_path)
    if manifest.get("ci") != expected or not _ci_gate_matches(expected):
        failures.append("Lean backend CI gate is missing or misconfigured.")


def _ci_gate_matches(ci: dict[str, Any]) -> bool:
    return ci == CI_GATE


def _manifest_sha256(manifest: dict[str, Any]) -> str:
    payload = {
        key: value for key, value in manifest.items() if key != "manifest_sha256"
    }
    return stable_sha256(payload)


def _read_json_object(
    path: Path,
    label: str,
    failures: list[str],
) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"{label} is missing: {path.as_posix()}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(f"{label} is invalid JSON at line {exc.lineno}.")
        return {}
    if not isinstance(payload, dict):
        failures.append(f"{label} must be a JSON object.")
        return {}
    return payload


def _resolve_path(path: Path, root: Path) -> Path:
    return path if path.is_absolute() else root / path


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_or_empty(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []
