from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.integrations.task_metadata import (
    normalize_task_metadata,
    task_metadata_for_plan,
)
from agades_pqc_gym.rl.environment import (
    REWARD_TERMS,
    build_formal_artifact_binding,
    score_attack_plan_candidate,
)

PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_DIR / "data"
TASK_PLAN_PATHS = sorted(DATA_DIR.glob("*.json"))
PRIME_REWARD_REPORT_SCHEMA = "agades.pqc.prime.reward_report.v1"
PRIME_RUBRIC_TERMS = ("accepted_attack_plan", "single_json_object", *REWARD_TERMS)
STRICT_REWARD_PROFILE = "strict"
PEDAGOGICAL_DENSE_REWARD_PROFILE = "pedagogical_dense"
FORMAT_REPAIR_DENSE_REWARD_PROFILE = "format_repair_dense"
PRIME_REWARD_PROFILES = (
    STRICT_REWARD_PROFILE,
    PEDAGOGICAL_DENSE_REWARD_PROFILE,
    FORMAT_REPAIR_DENSE_REWARD_PROFILE,
)
_STRICT_RUBRIC_WEIGHTS = {
    "accepted_attack_plan": 1.0,
    "single_json_object": 0.0,
    **dict.fromkeys(REWARD_TERMS, 0.0),
}
_PEDAGOGICAL_DENSE_RUBRIC_WEIGHTS = {
    "accepted_attack_plan": 0.30,
    "single_json_object": 0.10,
    "formal_validity": 0.15,
    "cryptographic_applicability": 0.10,
    "no_security_overclaim": 0.10,
    "student_readability": 0.07,
    "reproducibility": 0.05,
    "reviewer_quality": 0.05,
    "task_match": 0.04,
    "proof_obligation_coverage": 0.04,
}
_FORMAT_REPAIR_DENSE_RUBRIC_WEIGHTS = {
    "accepted_attack_plan": 0.20,
    "single_json_object": 0.20,
    "formal_validity": 0.20,
    "cryptographic_applicability": 0.05,
    "no_security_overclaim": 0.15,
    "student_readability": 0.08,
    "reproducibility": 0.03,
    "reviewer_quality": 0.03,
    "task_match": 0.04,
    "proof_obligation_coverage": 0.02,
}
_RUBRIC_WEIGHTS_BY_PROFILE = {
    STRICT_REWARD_PROFILE: _STRICT_RUBRIC_WEIGHTS,
    PEDAGOGICAL_DENSE_REWARD_PROFILE: _PEDAGOGICAL_DENSE_RUBRIC_WEIGHTS,
    FORMAT_REPAIR_DENSE_REWARD_PROFILE: _FORMAT_REPAIR_DENSE_RUBRIC_WEIGHTS,
}
SYSTEM_PROMPT = (
    "You submit JSON AttackPlan candidates for Agades PQC Gym. "
    "Return only a single AttackPlan JSON object. Do not submit Python, shell, "
    "network requests, exploit chains, or live-target instructions."
)
DEFAULT_PROMPT_PROFILE = "attackplan_json"
FORMAT_FIRST_PROMPT_PROFILE = "format_first_copy_seed"
FORMAT_REPAIR_PROMPT_PROFILE = "format_repair_extract_seed"
CLAIMS_GUARD_REPAIR_PROMPT_PROFILE = "claims_guard_repair"
CLAIMS_GUARD_FORMAT_REPAIR_PROMPT_PROFILE = "claims_guard_format_repair"
CLAIMS_GUARD_DECOY_FORMAT_REPAIR_PROMPT_PROFILE = (
    "claims_guard_decoy_format_repair"
)
PROMPT_PROFILES = (
    DEFAULT_PROMPT_PROFILE,
    FORMAT_FIRST_PROMPT_PROFILE,
    FORMAT_REPAIR_PROMPT_PROFILE,
    CLAIMS_GUARD_REPAIR_PROMPT_PROFILE,
    CLAIMS_GUARD_FORMAT_REPAIR_PROMPT_PROFILE,
    CLAIMS_GUARD_DECOY_FORMAT_REPAIR_PROMPT_PROFILE,
)


def build_dataset_rows(
    num_examples: int | None = None,
    *,
    attack_plan_id: str | None = None,
    target_family: str | None = None,
    seed_accepted: bool | None = None,
    prompt_profile: str = DEFAULT_PROMPT_PROFILE,
) -> list[dict[str, Any]]:
    _validate_prompt_profile(prompt_profile)
    rows = [
        _row_for_plan(path, prompt_profile=prompt_profile)
        for path in TASK_PLAN_PATHS
    ]
    if attack_plan_id is not None:
        rows = [
            row
            for row in rows
            if row["info"]["attack_plan_id"] == attack_plan_id
        ]
    if target_family is not None:
        rows = [
            row
            for row in rows
            if row["info"]["target_family"] == target_family
        ]
    if seed_accepted is not None:
        rows = [
            row
            for row in rows
            if row["info"]["seed_accepted"] is seed_accepted
        ]
    if not rows:
        filters = {
            "attack_plan_id": attack_plan_id,
            "target_family": target_family,
            "seed_accepted": seed_accepted,
        }
        raise ValueError(f"Prime environment task filter matched no rows: {filters}")
    if num_examples is None or num_examples < 0:
        return rows
    return rows[:num_examples]


def score_attack_plan_completion(
    completion: list[dict[str, Any]],
    *,
    info: dict[str, Any] | str | None = None,
    require_info: bool = False,
    project_root: Path | str | None = None,
    reward_profile: str = STRICT_REWARD_PROFILE,
) -> float:
    return float(
        score_attack_plan_completion_report(
            completion,
            info=info,
            require_info=require_info,
            project_root=project_root,
            reward_profile=reward_profile,
        )["aggregate_reward"]
    )


def score_attack_plan_completion_report(
    completion: list[dict[str, Any]],
    *,
    info: dict[str, Any] | str | None = None,
    require_info: bool = False,
    project_root: Path | str | None = None,
    reward_profile: str = STRICT_REWARD_PROFILE,
) -> dict[str, Any]:
    weights = _weights_by_term(reward_profile)
    completion_text = _last_content(completion)
    candidate = _single_json_object_text(completion_text)
    if candidate is None:
        if reward_profile == FORMAT_REPAIR_DENSE_REWARD_PROFILE:
            return _format_repair_reward_report(
                completion_text,
                info=info,
                project_root=project_root,
                reward_profile=reward_profile,
            )
        return _blocked_reward_report(
            "single_json_object",
            reward_profile=reward_profile,
        )

    root = _project_root(project_root)
    reward_report = score_attack_plan_candidate(
        candidate,
        task_info=normalize_task_metadata(info),
        require_task_match=require_info or info is not None,
        root=root,
    )
    formal_artifact_binding = build_formal_artifact_binding(
        candidate,
        root=root,
    )
    rubric_scores = {
        "accepted_attack_plan": float(reward_report["reward"]),
        "single_json_object": 1.0,
        **{
            term: float(reward_report["terms"][term])
            for term in REWARD_TERMS
        },
    }
    return _prime_reward_report(
        aggregate_reward=_weighted_reward(rubric_scores, weights),
        accepted=bool(reward_report["accepted"]),
        single_json_object=True,
        reward_profile=reward_profile,
        rubric_scores=rubric_scores,
        blocking_reasons=list(reward_report["blocking_reasons"]),
        reward_report=reward_report,
        formal_artifact_binding=formal_artifact_binding,
    )


def build_rubric_functions(
    *,
    project_root: Path | str | None = None,
    reward_profile: str = STRICT_REWARD_PROFILE,
) -> list[Any]:
    root = _project_root(project_root)
    _weights_by_term(reward_profile)

    async def accepted_attack_plan(
        completion: list[dict[str, Any]],
        info: dict[str, Any] | str | None = None,
        **_: Any,
    ) -> float:
        return _rubric_score(
            completion,
            "accepted_attack_plan",
            info=info,
            project_root=root,
            reward_profile=reward_profile,
        )

    functions = [accepted_attack_plan]
    functions.append(
        _build_term_rubric_function(
            "single_json_object",
            project_root=root,
            reward_profile=reward_profile,
        )
    )
    for term in REWARD_TERMS:
        functions.append(
            _build_term_rubric_function(
                term,
                project_root=root,
                reward_profile=reward_profile,
            )
        )
    return functions


def load_environment(
    num_examples: int = -1,
    project_root: Path | str | None = None,
    attack_plan_id: str | None = None,
    target_family: str | None = None,
    seed_accepted: bool | None = None,
    prompt_profile: str = DEFAULT_PROMPT_PROFILE,
    reward_profile: str = STRICT_REWARD_PROFILE,
    **kwargs: Any,
) -> Any:
    try:
        import verifiers as vf
        from datasets import Dataset
    except ImportError as exc:
        raise RuntimeError(
            "Prime Verifiers environment requires optional packages "
            "`verifiers` and `datasets`. Install this environment from "
            "`prime_intellect/verifiers_environment`."
        ) from exc

    dataset = Dataset.from_list(
        build_dataset_rows(
            num_examples=num_examples,
            attack_plan_id=attack_plan_id,
            target_family=target_family,
            seed_accepted=seed_accepted,
            prompt_profile=prompt_profile,
        )
    )
    rubric = vf.Rubric(
        funcs=build_rubric_functions(
            project_root=project_root,
            reward_profile=reward_profile,
        ),
        weights=build_rubric_weights(reward_profile),
    )
    return vf.SingleTurnEnv(
        dataset=dataset,
        rubric=rubric,
        system_prompt=SYSTEM_PROMPT,
        **kwargs,
    )


def _row_for_plan(path: Path, *, prompt_profile: str) -> dict[str, Any]:
    raw_json = path.read_text(encoding="utf-8")
    plan = AttackPlan.model_validate_json(raw_json)
    info = task_metadata_for_plan(
        plan,
        source_path=str(path.relative_to(PACKAGE_DIR)),
        seed_attack_plan_json=raw_json,
    )
    question = _question_for_seed_attack_plan(raw_json, prompt_profile=prompt_profile)
    return {
        "prompt": [{"role": "user", "content": question}],
        "answer": (
            "accepted" if info["seed_accepted"] else info["seed_evaluation_status"]
        ),
        "info": info,
    }


def _question_for_seed_attack_plan(raw_json: str, *, prompt_profile: str) -> str:
    if prompt_profile == DEFAULT_PROMPT_PROFILE:
        return "\n".join(
            [
                "Submit exactly one AttackPlan JSON object for the target below.",
                "Do not submit Python or any executable code.",
                "Do not invent pre-evaluation estimates. Keep claims unknown "
                "unless the JSON already contains reviewed external_claim "
                "evidence with a source.",
                "Toy/demo verifier output only; do not claim real-world PQC breaks.",
                "",
                "Seed AttackPlan:",
                raw_json,
            ]
        )
    if prompt_profile == FORMAT_FIRST_PROMPT_PROFILE:
        return "\n".join(
            [
                "Return the Seed AttackPlan below unchanged as exactly one "
                "JSON object.",
                "Preserve every field, value, key spelling, and array item.",
                "Do not add markdown, prose, analysis, comments, or code fences.",
                "The first non-whitespace character must be { and the final "
                "non-whitespace character must be }.",
                "Toy/demo verifier output only; do not claim real-world PQC breaks.",
                "",
                "Seed AttackPlan:",
                raw_json,
            ]
        )
    if prompt_profile == FORMAT_REPAIR_PROMPT_PROFILE:
        return "\n".join(
            [
                "Repair the broken model output below.",
                "It contains one public toy AttackPlan JSON object wrapped in "
                "extra prose and a markdown code fence.",
                "Return only the corrected AttackPlan JSON object.",
                "Do not include markdown, prose, analysis, comments, code "
                "fences, or wrapper text.",
                "The first non-whitespace character must be { and the final "
                "non-whitespace character must be }.",
                "Toy/demo verifier output only; do not claim real-world PQC breaks.",
                "",
                "Broken model output:",
                "Here is the AttackPlan candidate:",
                "```json",
                raw_json,
                "```",
                "This is only a toy/demo verifier example, not a security claim.",
            ]
        )
    if prompt_profile == CLAIMS_GUARD_REPAIR_PROMPT_PROFILE:
        return "\n".join(
            [
                "Repair the invalid AttackPlan JSON object below.",
                "It is invalid because claims contains pre-evaluation estimates "
                "without reviewed external_claim evidence.",
                "Return exactly one valid AttackPlan JSON object.",
                "Repair claims by setting estimated_time_bits=null, "
                "estimated_memory_bits=null, and success_probability=null.",
                "Do not add external_claim or source.",
                "Preserve target, operators, constraints, metadata, and "
                "attack_plan_id exactly.",
                "Do not include markdown, prose, analysis, comments, code "
                "fences, or wrapper text.",
                "The first non-whitespace character must be { and the final "
                "non-whitespace character must be }.",
                "Toy/demo verifier output only; do not claim real-world PQC breaks.",
                "",
                "Invalid AttackPlan JSON:",
                _claims_guard_invalid_output(raw_json),
            ]
        )
    if prompt_profile == CLAIMS_GUARD_FORMAT_REPAIR_PROMPT_PROFILE:
        return "\n".join(
            [
                "Repair the broken model output below.",
                "It contains one public toy AttackPlan JSON object wrapped in "
                "extra prose and a markdown code fence.",
                "The embedded AttackPlan is invalid because claims contains "
                "pre-evaluation estimates without reviewed external_claim "
                "evidence.",
                "Return only the corrected AttackPlan JSON object.",
                "Repair claims by setting estimated_time_bits=null, "
                "estimated_memory_bits=null, and success_probability=null.",
                "Do not add external_claim or source.",
                "Preserve target, operators, constraints, metadata, and "
                "attack_plan_id exactly.",
                "Do not include markdown, prose, analysis, comments, code "
                "fences, or wrapper text.",
                "The first non-whitespace character must be { and the final "
                "non-whitespace character must be }.",
                "Toy/demo verifier output only; do not claim real-world PQC breaks.",
                "",
                "Broken model output:",
                _claims_guard_wrapped_invalid_output(raw_json),
            ]
        )
    if prompt_profile == CLAIMS_GUARD_DECOY_FORMAT_REPAIR_PROMPT_PROFILE:
        return "\n".join(
            [
                "Repair the broken model output below.",
                "Ignore the decoy JSON object; it is not an AttackPlan.",
                "The correct public toy AttackPlan appears later inside a "
                "markdown code fence.",
                "The embedded AttackPlan is invalid because claims contains "
                "pre-evaluation estimates without reviewed external_claim "
                "evidence.",
                "Return only the corrected AttackPlan JSON object.",
                "Repair claims by setting estimated_time_bits=null, "
                "estimated_memory_bits=null, and success_probability=null.",
                "Do not add external_claim or source.",
                "Preserve target, operators, constraints, metadata, and "
                "attack_plan_id exactly.",
                "Do not include markdown, prose, analysis, comments, code "
                "fences, or wrapper text.",
                "The first non-whitespace character must be { and the final "
                "non-whitespace character must be }.",
                "Toy/demo verifier output only; do not claim real-world PQC breaks.",
                "",
                "Broken model output:",
                _claims_guard_decoy_wrapped_invalid_output(raw_json),
            ]
        )
    raise ValueError(f"unsupported Prime prompt profile: {prompt_profile}")


def _validate_prompt_profile(prompt_profile: str) -> None:
    if prompt_profile not in PROMPT_PROFILES:
        raise ValueError(f"unsupported Prime prompt profile: {prompt_profile}")


def build_rubric_weights(
    reward_profile: str = STRICT_REWARD_PROFILE,
) -> list[float]:
    weights = _weights_by_term(reward_profile)
    return [weights[term] for term in PRIME_RUBRIC_TERMS]


def _last_content(completion: list[dict[str, Any]]) -> str:
    if not completion:
        return ""
    content = completion[-1].get("content", "")
    return content if isinstance(content, str) else ""


def _single_json_object_text(text: str) -> str | None:
    stripped = text.strip()
    if not stripped.startswith("{"):
        return None

    decoder = json.JSONDecoder()
    try:
        value, end = decoder.raw_decode(stripped)
    except json.JSONDecodeError:
        return None
    if not isinstance(value, dict):
        return None
    if stripped[end:].strip():
        return None
    return stripped


def _build_term_rubric_function(
    term: str,
    *,
    project_root: Path | None,
    reward_profile: str,
) -> Any:
    async def score_term(
        completion: list[dict[str, Any]],
        info: dict[str, Any] | str | None = None,
        **_: Any,
    ) -> float:
        return _rubric_score(
            completion,
            term,
            info=info,
            project_root=project_root,
            reward_profile=reward_profile,
        )

    score_term.__name__ = term
    return score_term


def _rubric_score(
    completion: list[dict[str, Any]],
    term: str,
    *,
    info: dict[str, Any] | str | None,
    project_root: Path | None,
    reward_profile: str = STRICT_REWARD_PROFILE,
) -> float:
    report = score_attack_plan_completion_report(
        completion,
        info=info,
        require_info=True,
        project_root=project_root,
        reward_profile=reward_profile,
    )
    return float(report["rubric_scores"][term])


def _project_root(project_root: Path | str | None) -> Path | None:
    if project_root is None:
        if _has_required_formal_artifacts(PACKAGE_DIR):
            return PACKAGE_DIR
        return None
    root = Path(project_root).expanduser().resolve()
    _require_formal_artifacts(root)
    return root


def _has_required_formal_artifacts(root: Path) -> bool:
    return all(path.exists() for path in _required_formal_artifact_paths(root))


def _require_formal_artifacts(root: Path) -> None:
    missing = [
        path
        for path in _required_formal_artifact_paths(root)
        if not path.exists()
    ]
    if missing:
        missing_labels = ", ".join(str(path) for path in missing)
        raise ValueError(
            "project_root does not contain required Agades formal artifacts: "
            f"{missing_labels}"
        )


def _required_formal_artifact_paths(root: Path) -> tuple[Path, ...]:
    return (
        root / "docs" / "formal_attackplan_semantics.json",
        root / "docs" / "formal_operator_semantics.json",
        root / "docs" / "formal_estimator_model.json",
        root / "formal" / "lean" / "AgadesPQC" / "AttackPlan.lean",
    )


def _weights_by_term(reward_profile: str) -> dict[str, float]:
    try:
        weights = _RUBRIC_WEIGHTS_BY_PROFILE[reward_profile]
    except KeyError as exc:
        expected = ", ".join(PRIME_REWARD_PROFILES)
        raise ValueError(
            f"unknown Prime reward profile: {reward_profile!r}; "
            f"expected one of: {expected}"
        ) from exc
    if set(weights) != set(PRIME_RUBRIC_TERMS):
        raise RuntimeError(f"Prime reward profile is malformed: {reward_profile}")
    total_weight = sum(weights.values())
    if abs(total_weight - 1.0) > 1e-12:
        raise RuntimeError(
            f"Prime reward profile weights must sum to 1.0: {reward_profile}"
        )
    return weights


def _weighted_reward(
    rubric_scores: dict[str, float],
    weights: dict[str, float],
) -> float:
    return float(
        sum(float(rubric_scores[term]) * weight for term, weight in weights.items())
    )


def _format_repair_reward_report(
    text: str,
    *,
    info: dict[str, Any] | str | None,
    project_root: Path | str | None,
    reward_profile: str,
) -> dict[str, Any]:
    embedded_json = _embedded_json_object_text(text)
    root = _project_root(project_root)
    normalized_info = normalize_task_metadata(info)
    rubric_scores = dict.fromkeys(PRIME_RUBRIC_TERMS, 0.0)
    rubric_scores["no_security_overclaim"] = _no_security_overclaim_score(text)
    rubric_scores["student_readability"] = _format_readability_score(text)

    blocking_reasons = ["single_json_object"]
    reward_report = None
    formal_artifact_binding = None
    if embedded_json is not None:
        reward_report = score_attack_plan_candidate(
            embedded_json,
            task_info=normalized_info,
            require_task_match=info is not None,
            root=root,
        )
        formal_artifact_binding = build_formal_artifact_binding(
            embedded_json,
            root=root,
        )
        rubric_scores.update(
            {
                "accepted_attack_plan": float(reward_report["reward"]) * 0.5,
                "formal_validity": float(
                    reward_report["terms"]["formal_validity"]
                ),
                "cryptographic_applicability": float(
                    reward_report["terms"]["cryptographic_applicability"]
                )
                * 0.5,
                "no_security_overclaim": float(
                    reward_report["terms"]["no_security_overclaim"]
                ),
                "student_readability": max(
                    rubric_scores["student_readability"],
                    0.5 * float(reward_report["terms"]["student_readability"]),
                ),
                "reproducibility": 0.5
                * float(reward_report["terms"]["reproducibility"]),
                "reviewer_quality": 0.5
                * float(reward_report["terms"]["reviewer_quality"]),
                "task_match": float(reward_report["terms"]["task_match"]),
                "proof_obligation_coverage": 0.5
                * float(reward_report["terms"]["proof_obligation_coverage"]),
            }
        )
        if reward_report["accepted"]:
            blocking_reasons.append("wrapped_or_prefixed_json")
        else:
            blocking_reasons.extend(reward_report["blocking_reasons"])

    weights = _weights_by_term(reward_profile)
    return _prime_reward_report(
        aggregate_reward=_weighted_reward(rubric_scores, weights),
        accepted=False,
        single_json_object=False,
        reward_profile=reward_profile,
        rubric_scores=rubric_scores,
        blocking_reasons=blocking_reasons,
        reward_report=reward_report,
        formal_artifact_binding=formal_artifact_binding,
    )


def _embedded_json_object_text(text: str) -> str | None:
    decoder = json.JSONDecoder()
    for index, character in enumerate(text):
        if character != "{":
            continue
        try:
            value, end = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return text[index : index + end]
    return None


def _claims_guard_invalid_output(raw_json: str) -> str:
    payload = json.loads(raw_json)
    claims = payload.get("claims")
    if not isinstance(claims, dict):
        claims = {}
        payload["claims"] = claims
    claims["estimated_time_bits"] = 64.0
    claims["estimated_memory_bits"] = 32.0
    claims["success_probability"] = 0.5
    claims.pop("external_claim", None)
    claims.pop("source", None)
    return json.dumps(payload, indent=2)


def _claims_guard_wrapped_invalid_output(raw_json: str) -> str:
    return "\n".join(
        [
            "Here is the AttackPlan candidate:",
            "```json",
            _claims_guard_invalid_output(raw_json),
            "```",
            "This is only a toy/demo verifier example, not a security claim.",
        ]
    )


def _claims_guard_decoy_wrapped_invalid_output(raw_json: str) -> str:
    decoy = {
        "not_an_attack_plan": True,
        "claims": {
            "estimated_time_bits": 64.0,
            "estimated_memory_bits": 32.0,
            "success_probability": 0.5,
        },
    }
    return "\n".join(
        [
            "Candidate object 1:",
            json.dumps(decoy, indent=2),
            "",
            "Candidate object 2:",
            "```json",
            _claims_guard_invalid_output(raw_json),
            "```",
            "Only candidate object 2 is the toy/demo AttackPlan to repair.",
        ]
    )


def _no_security_overclaim_score(text: str) -> float:
    lowered = text.lower()
    banned_fragments = (
        "breaks kyber",
        "breaks dilithium",
        "breaks ml-kem",
        "breaks ml-dsa",
        "pqc is broken",
        "real-world break",
    )
    return 0.0 if any(fragment in lowered for fragment in banned_fragments) else 1.0


def _format_readability_score(text: str) -> float:
    stripped = text.strip()
    if not stripped:
        return 0.0
    score = 0.0
    if stripped.startswith("{"):
        score += 0.4
    if stripped.endswith("}"):
        score += 0.4
    if "```" not in stripped:
        score += 0.2
    return score


def _blocked_reward_report(
    reason: str,
    *,
    reward_profile: str,
) -> dict[str, Any]:
    return _prime_reward_report(
        aggregate_reward=0.0,
        accepted=False,
        single_json_object=False,
        reward_profile=reward_profile,
        rubric_scores=dict.fromkeys(PRIME_RUBRIC_TERMS, 0.0),
        blocking_reasons=[reason],
        reward_report=None,
        formal_artifact_binding=None,
    )


def _prime_reward_report(
    *,
    aggregate_reward: float,
    accepted: bool,
    single_json_object: bool,
    reward_profile: str,
    rubric_scores: dict[str, float],
    blocking_reasons: list[str],
    reward_report: dict[str, Any] | None,
    formal_artifact_binding: dict[str, Any] | None,
) -> dict[str, Any]:
    binding = formal_artifact_binding or {}
    return {
        "schema_version": PRIME_REWARD_REPORT_SCHEMA,
        "aggregate_reward": aggregate_reward,
        "accepted": accepted,
        "single_json_object": single_json_object,
        "reward_profile": reward_profile,
        "rubric_scores": rubric_scores,
        "blocking_reasons": blocking_reasons,
        "formal_summary": (
            reward_report.get("formal_summary", {}) if reward_report else {}
        ),
        "formal_artifact_binding": binding,
        "review_governance_ok": binding.get("review_governance_ok") is True,
    }
