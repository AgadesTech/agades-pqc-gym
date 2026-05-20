from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.evaluators.lattice_estimator import LATTICE_ESTIMATOR_PINNED_COMMIT
from agades_pqc_gym.evaluators.lattice_estimator_checkout import (
    LATTICE_ESTIMATOR_REPOSITORY,
    inspect_lattice_estimator_checkout,
)
from agades_pqc_gym.evolution.scheduler import validate_policy_private_path

LATTICE_ESTIMATOR_CHECKOUT_PREFLIGHT_SCHEMA = (
    "agades.pqc.lattice_estimator_checkout_preflight.v1"
)
DEFAULT_CHECKOUT_PREFLIGHT_PATH = Path(
    "private/reports/lattice_estimator_checkout_preflight.json"
)


def build_lattice_estimator_checkout_preflight(
    *,
    source_path: Path,
    report_path: Path | None = None,
    required_commit: str = LATTICE_ESTIMATOR_PINNED_COMMIT,
) -> dict[str, Any]:
    inspection = inspect_lattice_estimator_checkout(
        source_path,
        required_commit=required_commit,
    )
    return {
        "schema_version": LATTICE_ESTIMATOR_CHECKOUT_PREFLIGHT_SCHEMA,
        "created_at": "manual-checkout-preflight-recorded",
        "report": {
            "path": (report_path or DEFAULT_CHECKOUT_PREFLIGHT_PATH).as_posix(),
            "private": True,
        },
        "upstream": {
            "repository": LATTICE_ESTIMATOR_REPOSITORY,
            "pinned_commit": required_commit,
            "pin_source": "docs/lattice_estimator_manifest.json",
        },
        "source_checkout": {
            "path": inspection.source_path.as_posix(),
            "git": {
                "head_commit": inspection.head_commit,
                "head_matches_required_pin": inspection.head_matches_required_pin,
                "remote_origin": inspection.remote_origin,
                "remote_matches_upstream": inspection.remote_matches_upstream,
                "working_tree_clean": inspection.working_tree_clean,
            },
            "python_entrypoints": {
                "estimator_package": inspection.estimator_package,
                "estimator_module": inspection.estimator_module,
            },
        },
        "readiness": {
            "ready_for_private_baseline_run": inspection.ready,
            "requires_expert_review_before_publication": True,
            "failure_count": len(inspection.failures),
        },
        "safety": {
            "imports_upstream_python": False,
            "executes_estimator": False,
            "numeric_reference_outputs_committed": False,
            "publication_allowed": False,
            "security_claim": False,
            "writes_only_allowed_private_roots": True,
        },
        "failures": list(inspection.failures),
    }


def write_lattice_estimator_checkout_preflight(
    out: Path,
    *,
    source_path: Path,
    policy: dict[str, Any],
    policy_root: Path | None = None,
    required_commit: str = LATTICE_ESTIMATOR_PINNED_COMMIT,
) -> dict[str, Any]:
    output_root = (policy_root or Path.cwd()).resolve()
    validate_policy_private_path(out, policy=policy, root=output_root)
    report = build_lattice_estimator_checkout_preflight(
        source_path=source_path,
        report_path=out,
        required_commit=required_commit,
    )
    resolved_out = out if out.is_absolute() else output_root / out
    resolved_out.parent.mkdir(parents=True, exist_ok=True)
    resolved_out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report
