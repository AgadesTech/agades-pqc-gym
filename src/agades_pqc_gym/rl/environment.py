from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.target import TargetFamily
from agades_pqc_gym.formal.artifacts import (
    build_attack_plan_proof_artifact_from_json,
)
from agades_pqc_gym.formal.attack_plan_semantics import (
    DEFAULT_ATTACKPLAN_SEMANTICS_PATH,
    verify_formal_attackplan_semantics,
)
from agades_pqc_gym.formal.family_coverage import REPRESENTATIVE_ATTACK_PLANS
from agades_pqc_gym.integrations.task_metadata import (
    attack_plan_matches_task_metadata,
    normalize_task_metadata,
    task_metadata_for_plan,
)
from agades_pqc_gym.rl.pedagogy import build_pedagogical_reward_report
from agades_pqc_gym.utils.validation_errors import stable_validation_error_messages
from agades_pqc_gym.verifier import verify_attack_plan_json

RL_REWARD_REPORT_SCHEMA = "agades.pqc.rl.reward_report.v1"
ROLLOUT_TRACE_SCHEMA = "agades.pqc.rl.rollout_trace.v1"
OBSERVATION_SCHEMA = "agades.pqc.rl.observation.v1"
FORMAL_ARTIFACT_BINDING_SCHEMA = "agades.pqc.rl.formal_artifact_binding.v1"
ATTACKPLAN_SEMANTICS_BINDING_SCHEMA = (
    "agades.pqc.rl.attackplan_semantics_binding.v1"
)
ROOT = Path(__file__).resolve().parents[3]
REWARD_TERMS = (
    "formal_validity",
    "cryptographic_applicability",
    "no_security_overclaim",
    "student_readability",
    "reproducibility",
    "reviewer_quality",
    "task_match",
    "proof_obligation_coverage",
)
DEFAULT_ROLLOUT_PLANS = [
    REPRESENTATIVE_ATTACK_PLANS[family] for family in TargetFamily
]


class AgadesPQCGymEnvironment:
    """Small public-safe single-step RL environment over AttackPlan tasks."""

    def __init__(
        self,
        tasks: list[dict[str, Any]],
        *,
        root: Path | None = None,
    ) -> None:
        if not tasks:
            raise ValueError("AgadesPQCGymEnvironment requires at least one task.")
        self._tasks = tasks
        self._root = root
        self._current_task: dict[str, Any] | None = None

    @classmethod
    def from_attack_plan_paths(
        cls,
        paths: list[Path],
        *,
        root: Path | None = None,
    ) -> AgadesPQCGymEnvironment:
        project_root = root.resolve() if root is not None else None
        return cls(
            [
                _task_from_path(
                    _resolve_attack_plan_path(path, project_root),
                    source_path=_source_path_label(path, project_root),
                )
                for path in paths
            ],
            root=project_root,
        )

    def reset(self, index: int = 0) -> dict[str, Any]:
        if index < 0 or index >= len(self._tasks):
            raise IndexError("task index out of range")
        task = self._tasks[index]
        self._current_task = task
        return {
            "schema_version": OBSERVATION_SCHEMA,
            "task": task,
            "prompt": _prompt_for_task(task),
            "safety": {
                "accepts_executable_code": False,
                "accepts_live_targets": False,
                "security_claims_allowed": False,
                "private_data_allowed": False,
            },
        }

    def step(self, candidate_json: str) -> dict[str, Any]:
        if self._current_task is None:
            self.reset()
        assert self._current_task is not None
        reward_report = score_attack_plan_candidate(
            candidate_json,
            task_info=self._current_task,
            require_task_match=True,
            root=self._root,
        )
        trace = _rollout_trace(
            self._current_task,
            candidate_json,
            reward_report,
            root=self._root,
        )
        return {
            "observation": None,
            "reward": reward_report["reward"],
            "done": True,
            "info": {
                "reward_report": reward_report,
                "trace": trace,
            },
        }


def score_attack_plan_candidate(
    candidate_json: str,
    *,
    task_info: dict[str, Any] | str | None = None,
    require_task_match: bool = False,
    pedagogical_signals: dict[str, Any] | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    parsed_task = normalize_task_metadata(task_info)
    plan: AttackPlan | None = None
    validation_errors: list[str] = []
    try:
        plan = AttackPlan.model_validate_json(candidate_json)
    except ValidationError as exc:
        validation_errors.extend(stable_validation_error_messages(exc))
    except ValueError as exc:
        validation_errors.append(str(exc))

    verifier_result = verify_attack_plan_json(candidate_json)
    formal_summary = _formal_summary(candidate_json, plan, root=root)
    task_match = (
        _task_match(plan, parsed_task)
        if parsed_task is not None
        else (not require_task_match)
    )
    terms = {
        "formal_validity": _bool_score(
            plan is not None and formal_summary["accepted"]
        ),
        "cryptographic_applicability": _bool_score(
            verifier_result["accepted"] is True
        ),
        "no_security_overclaim": _bool_score(
            plan is not None and _no_security_overclaim(plan, verifier_result)
        ),
        "student_readability": _bool_score(
            plan is not None and _student_readable(candidate_json, plan)
        ),
        "reproducibility": _reproducibility_score(verifier_result, parsed_task),
        "reviewer_quality": _bool_score(
            formal_summary["required_reviewers"] >= 3
            and formal_summary["claim_boundary_ok"] is True
        ),
        "task_match": _bool_score(task_match),
        "proof_obligation_coverage": _proof_obligation_coverage_score(
            formal_summary
        ),
    }
    blocking_reasons = _blocking_reasons(
        verifier_result=verifier_result,
        terms=terms,
        require_task_match=require_task_match,
        task_info=parsed_task,
    )
    base_reward = 0.0 if blocking_reasons else _mean_reward(terms)
    pedagogical_reward = build_pedagogical_reward_report(
        base_reward,
        pedagogical_signals,
    )
    if pedagogical_reward["signal_error"]:
        blocking_reasons.append("pedagogical_signals")
    reward = 0.0 if blocking_reasons else pedagogical_reward["final_reward"]
    return {
        "schema_version": RL_REWARD_REPORT_SCHEMA,
        "reward": reward,
        "accepted": reward > 0.0 and not blocking_reasons,
        "blocked": bool(blocking_reasons),
        "blocking_reasons": blocking_reasons,
        "terms": terms,
        "pedagogical_reward": pedagogical_reward,
        "formal_summary": formal_summary,
        "verifier_summary": {
            "schema_valid": verifier_result["schema_valid"],
            "accepted": verifier_result["accepted"],
            "evaluation_status": verifier_result["evaluation_status"],
            "target_family": verifier_result["target_family"],
            "safety": verifier_result["safety"],
        },
        "claim_boundary": {
            "trains_agent_behavior": True,
            "claims_pqc_break": False,
            "requires_human_review_before_claim": True,
        },
        "validation_errors": validation_errors,
    }


def build_public_rollout_examples(
    paths: list[Path],
    *,
    root: Path | None = None,
) -> list[dict[str, Any]]:
    project_root = root.resolve() if root is not None else None
    rows: list[dict[str, Any]] = []
    for path in paths:
        resolved_path = _resolve_attack_plan_path(path, project_root)
        env = AgadesPQCGymEnvironment.from_attack_plan_paths(
            [path],
            root=project_root,
        )
        env.reset()
        step = env.step(resolved_path.read_text(encoding="utf-8"))
        rows.append(step["info"]["trace"])
    return rows


def write_public_rollout_examples(
    paths: list[Path],
    out: Path,
    *,
    root: Path | None = None,
) -> list[dict[str, Any]]:
    rows = build_public_rollout_examples(paths, root=root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return rows


def _resolve_attack_plan_path(path: Path, root: Path | None) -> Path:
    if root is not None and not path.is_absolute():
        return root / path
    return path


def _source_path_label(path: Path, root: Path | None) -> str:
    if root is None or not path.is_absolute():
        return path.as_posix()
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _task_from_path(path: Path, *, source_path: str | None = None) -> dict[str, Any]:
    raw_json = path.read_text(encoding="utf-8")
    plan = AttackPlan.model_validate_json(raw_json)
    return task_metadata_for_plan(
        plan,
        source_path=source_path or path.as_posix(),
        seed_attack_plan_json=raw_json,
    )


def _prompt_for_task(task: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "Return exactly one Agades PQC Gym AttackPlan JSON object. "
                "Do not include code, live targets, private traces, or PQC "
                "break claims."
            ),
        },
        {
            "role": "user",
            "content": (
                "Produce or repair an AttackPlan matching target_family="
                f"{task['target_family']}, target_name={task['target_name']}, "
                f"support_level={task['support_level']}, operators="
                f"{task['operator_types']}."
            ),
        },
    ]


def _formal_summary(
    candidate_json: str,
    plan: AttackPlan | None,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    attackplan_semantics = build_attackplan_semantics_binding(root=root)
    if plan is None:
        return {
            "accepted": False,
            "attackplan_semantics": attackplan_semantics,
            "family_invariants": 0,
            "proof_obligations": 0,
            "typed_proof_obligations": 0,
            "proof_obligation_type_rules": 0,
            "type_rule_kinds": [],
            "lean_theorems": 0,
            "required_reviewers": 0,
            "claim_boundary_ok": False,
        }
    artifact = build_attack_plan_proof_artifact_from_json(
        candidate_json,
        source_label="<rl-candidate>",
    )
    proof_obligations = artifact["proof_obligations"]
    family_invariants = artifact["family_invariants"]
    type_rules = artifact.get("proof_obligation_type_rules", [])
    type_rule_keys: set[str] = set()
    type_rule_kinds: set[str] = set()
    for rule in type_rules:
        type_rule_key = _type_rule_key(rule)
        if type_rule_key is None:
            continue
        type_rule_keys.add(type_rule_key)
        type_rule_kinds.add(rule["kind"])
    typed_proof_obligations = [
        obligation
        for obligation in proof_obligations
        if _obligation_has_matching_type_rule(obligation, type_rule_keys)
    ]
    return {
        "accepted": attackplan_semantics["accepted"] is True,
        "attackplan_semantics": attackplan_semantics,
        "family_invariants": len(family_invariants),
        "proof_obligations": len(proof_obligations),
        "typed_proof_obligations": len(typed_proof_obligations),
        "proof_obligation_type_rules": len(type_rules),
        "type_rule_kinds": sorted(type_rule_kinds),
        "lean_theorems": len(
            {
                obligation["lean_theorem"]
                for obligation in proof_obligations
                if obligation.get("lean_theorem")
            }
        ),
        "required_reviewers": len(artifact["review"]["required_reviewers"]),
        "claim_boundary_ok": (
            "not PQC break claims" in artifact["review"]["claim_boundary"]
        ),
    }


def _task_match(
    plan: AttackPlan | None,
    task_info: dict[str, Any] | None,
) -> bool:
    if plan is None or task_info is None:
        return False
    return attack_plan_matches_task_metadata(plan, task_info)


def _no_security_overclaim(
    plan: AttackPlan,
    verifier_result: dict[str, Any],
) -> bool:
    if verifier_result["safety"]["security_claim"] is not False:
        return False
    if plan.claims.external_claim:
        return False
    return (
        plan.claims.estimated_time_bits is None
        and plan.claims.estimated_memory_bits is None
        and plan.claims.success_probability is None
    )


def _proof_obligation_coverage_score(formal_summary: dict[str, Any]) -> float:
    proof_obligations = formal_summary["proof_obligations"]
    required_type_kinds = {
        "target_invariant",
        "operator_precondition",
        "schema_only_boundary",
        "family_applicability_boundary",
        "estimator_claim_boundary",
    }
    return _bool_score(
        proof_obligations > 0
        and formal_summary["family_invariants"] > 0
        and formal_summary["typed_proof_obligations"] == proof_obligations
        and required_type_kinds.issubset(set(formal_summary["type_rule_kinds"]))
    )


def _obligation_has_matching_type_rule(
    obligation: dict[str, Any],
    type_rule_keys: set[str],
) -> bool:
    obligation_type = obligation.get("obligation_type")
    type_rule = obligation.get("type_rule")
    if not isinstance(obligation_type, dict) or not isinstance(type_rule, dict):
        return False
    kind = obligation_type.get("kind")
    type_rule_key = _type_rule_key(type_rule)
    return isinstance(kind, str) and type_rule.get("kind") == kind and (
        type_rule_key in type_rule_keys
    )


def _type_rule_key(rule: object) -> str | None:
    if not isinstance(rule, dict):
        return None
    lean_source = rule.get("lean_source")
    lean_theorem = rule.get("lean_theorem")
    if (
        rule.get("schema_version")
        != "agades.pqc.formal.proof_obligation_type_rule.v1"
        or rule.get("backend") != "lean4"
        or not isinstance(rule.get("kind"), str)
        or not isinstance(lean_theorem, str)
        or not lean_theorem.startswith("AgadesPQC.ProofObligation.")
        or not isinstance(lean_source, dict)
        or lean_source.get("path") != "formal/lean/AgadesPQC/ProofObligation.lean"
        or not isinstance(lean_source.get("declaration"), str)
        or not isinstance(lean_source.get("sha256"), str)
        or not isinstance(rule.get("type_rule_sha256"), str)
    ):
        return None
    return json.dumps(rule, sort_keys=True, separators=(",", ":"))


def _student_readable(candidate_json: str, plan: AttackPlan) -> bool:
    stripped = candidate_json.strip()
    if not (stripped.startswith("{") and stripped.endswith("}")):
        return False
    if not plan.metadata.notes or len(plan.metadata.notes.strip()) < 10:
        return False
    notes = plan.metadata.notes.lower()
    return "security claim" in notes and ("not" in notes or "no " in notes)


def _reproducibility_score(
    verifier_result: dict[str, Any],
    task_info: dict[str, Any] | None,
) -> float:
    reproduction = verifier_result["reproduction"]
    if task_info and task_info.get("requires_reproducibility") is True:
        return _bool_score(reproduction["success"] is True)
    if verifier_result["schema_valid"] is not True:
        return 0.0
    return 1.0


def _blocking_reasons(
    *,
    verifier_result: dict[str, Any],
    terms: dict[str, float],
    require_task_match: bool,
    task_info: dict[str, Any] | None,
) -> list[str]:
    reasons: list[str] = []
    if verifier_result["schema_valid"] is not True:
        reasons.append("schema_valid")
    if terms["formal_validity"] != 1.0:
        reasons.append("formal_validity")
    if verifier_result["accepted"] is not True:
        reasons.append("cryptographic_applicability")
    if terms["no_security_overclaim"] != 1.0:
        reasons.append("no_security_overclaim")
    if terms["proof_obligation_coverage"] != 1.0:
        reasons.append("proof_obligation_coverage")
    if require_task_match and task_info is None:
        reasons.append("task_info")
    if terms["task_match"] != 1.0:
        reasons.append("task_match")
    return reasons


def _rollout_trace(
    task: dict[str, Any],
    candidate_json: str,
    reward_report: dict[str, Any],
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    candidate = _candidate_summary(candidate_json)
    return {
        "schema_version": ROLLOUT_TRACE_SCHEMA,
        "task": task,
        "candidate": candidate,
        "formal_artifact_binding": build_formal_artifact_binding(
            candidate_json,
            root=root,
        ),
        "reward_report": reward_report,
        "public_release_ok": True,
        "private_fields_present": False,
        "claim_boundary": {
            "claims_pqc_break": False,
            "human_review_required_before_claim": True,
        },
    }


def _candidate_summary(candidate_json: str) -> dict[str, Any]:
    sha256 = hashlib.sha256(candidate_json.encode("utf-8")).hexdigest()
    try:
        plan = AttackPlan.model_validate_json(candidate_json)
    except ValueError:
        return {
            "attack_plan_id": None,
            "target_family": None,
            "sha256": sha256,
        }
    return {
        "attack_plan_id": plan.attack_plan_id,
        "target_family": plan.target.family.value,
        "sha256": sha256,
    }


def build_formal_artifact_binding(
    candidate_json: str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    attackplan_semantics = build_attackplan_semantics_binding(root=root)
    try:
        artifact = build_attack_plan_proof_artifact_from_json(
            candidate_json,
            source_label="<rl-candidate>",
        )
    except (json.JSONDecodeError, ValidationError, ValueError):
        return {
            "schema_version": FORMAL_ARTIFACT_BINDING_SCHEMA,
            "status": "unavailable",
            "attack_plan_id": None,
            "family": None,
            "artifact_sha256": None,
            "family_invariant_ids": [],
            "proof_obligation_ids": [],
            "proof_obligation_sha256": [],
            "proof_obligation_type_rule_sha256": [],
            "attackplan_semantics": attackplan_semantics,
            "review_status": None,
            "required_reviewers": [],
            "claim_allowed": False,
            "claim_boundary": (
                "formal artifact unavailable for invalid candidate; no claim "
                "is allowed"
            ),
            "error_code": "formal_artifact_unavailable",
        }

    proof_obligations = artifact["proof_obligations"]
    type_rules = artifact["proof_obligation_type_rules"]
    review = artifact["review"]
    return {
        "schema_version": FORMAL_ARTIFACT_BINDING_SCHEMA,
        "status": "attached",
        "attack_plan_id": artifact["attack_plan"]["id"],
        "attack_plan_canonical_sha256": artifact["attack_plan"][
            "canonical_sha256"
        ],
        "family": artifact["family"],
        "artifact_sha256": artifact["artifact_sha256"],
        "family_invariant_ids": [
            invariant["invariant_id"]
            for invariant in artifact["family_invariants"]
        ],
        "proof_obligation_ids": [
            obligation["obligation_id"] for obligation in proof_obligations
        ],
        "proof_obligation_sha256": [
            obligation["obligation_sha256"] for obligation in proof_obligations
        ],
        "proof_obligation_type_rule_sha256": [
            rule["type_rule_sha256"] for rule in type_rules
        ],
        "attackplan_semantics": attackplan_semantics,
        "review_status": review["status"],
        "required_reviewers": review["required_reviewers"],
        "claim_allowed": False,
        "claim_boundary": review["claim_boundary"],
    }


def build_attackplan_semantics_binding(
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    verification = verify_formal_attackplan_semantics(
        DEFAULT_ATTACKPLAN_SEMANTICS_PATH,
        root=project_root,
    )
    contract = _read_attackplan_semantics_contract(project_root)
    claim_policy = contract.get("claim_policy", {})
    return {
        "schema_version": ATTACKPLAN_SEMANTICS_BINDING_SCHEMA,
        "semantics_path": DEFAULT_ATTACKPLAN_SEMANTICS_PATH.as_posix(),
        "accepted": verification["accepted"],
        "validation_rules": len(contract.get("validation_rules", [])),
        "formal_rules": len(contract.get("formal_rules", [])),
        "claim_policy_forbids_unreviewed_security_claims": (
            isinstance(claim_policy, dict)
            and claim_policy.get("security_claim_allowed_without_review") is False
        ),
        "semantics_sha256": contract.get("semantics_sha256"),
    }


def _read_attackplan_semantics_contract(root: Path) -> dict[str, Any]:
    try:
        payload = json.loads(
            (root / DEFAULT_ATTACKPLAN_SEMANTICS_PATH).read_text(encoding="utf-8")
        )
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _bool_score(value: bool) -> float:
    return 1.0 if value else 0.0


def _mean_reward(terms: dict[str, float]) -> float:
    if not terms:
        return 0.0
    return sum(terms.values()) / len(terms)
