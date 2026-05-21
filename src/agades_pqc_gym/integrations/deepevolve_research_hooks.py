from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from agades_pqc_gym.core.operators import ALLOWED_OPERATORS
from agades_pqc_gym.deepevolve_hooks.operator_proposals import (
    proposals_from_paper_card,
)
from agades_pqc_gym.deepevolve_hooks.paper_card import PaperCard, load_paper_cards

DEEPEVOLVE_RESEARCH_HOOKS_SCHEMA = "agades.pqc.deepevolve_research_hooks.v1"
DEEPEVOLVE_RESEARCH_HOOKS_VERIFICATION_SCHEMA = (
    "agades.pqc.deepevolve_research_hooks_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MANIFEST_PATH = Path("docs/deepevolve_research_hooks_manifest.json")
DEFAULT_PAPER_CARD_DIR = Path("examples/paper_cards")
_REQUIRED_FAMILIES = {
    "CODE_BASED",
    "HASH_BASED",
    "IMPLEMENTATION_SECURITY",
    "ISOGENY_HISTORICAL",
    "LWE",
    "MLWE",
    "MULTIVARIATE",
}
_REQUIRED_FALSE_SAFETY_FLAGS = (
    "arbitrary_code_execution",
    "contains_private_traces",
    "modifies_estimator_scores",
    "publishes_private_candidates",
    "research_claim",
)
PRIVATE_QWEN_PROPOSAL_ROLES = [
    "generate_attackplan",
    "mutate_attackplan",
    "critique_attackplan",
    "repair_attackplan",
    "draft_proof_obligations",
    "draft_family_invariants",
    "propose_evaluation_strategy",
]
PRIVATE_QWEN_RESEARCH_BINDING = {
    "model": "Qwen3.6-27B-private",
    "training_manifest": "docs/private_training_config_manifest.json",
    "pedagogical_rl_method": "docs/pedagogical_rl_method.json",
    "dataset_curation_manifest": "docs/private_dataset_curation.json",
    "proposal_roles": list(PRIVATE_QWEN_PROPOSAL_ROLES),
    "proposal_gate": {
        "attackplan_validation_required": True,
        "proof_obligation_generation_required": True,
        "estimator_compatibility_required": True,
        "human_review_required_before_claim": True,
    },
    "public_publication_allowed": False,
}


def build_deepevolve_research_hooks_manifest(
    paper_card_dir: Path | None = None,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    source_dir = _resolve_path(paper_card_dir or DEFAULT_PAPER_CARD_DIR, project_root)
    cards = load_paper_cards(source_dir)
    proposals = [
        proposal
        for card in cards
        for proposal in proposals_from_paper_card(card)
    ]
    families = sorted({card.family for card in cards})
    operator_count = sum(len(card.operators_suggested) for card in cards)
    return {
        "schema_version": DEEPEVOLVE_RESEARCH_HOOKS_SCHEMA,
        "project": {
            "name": "Agades PQC Gym",
            "package": "agades_pqc_gym",
            "repository": "https://github.com/AgadesTech/agades-pqc-gym",
        },
        "source": {
            "paper_card_directory": _display_path(source_dir),
            "input_format": "yaml_paper_cards",
        },
        "summary": {
            "all_cards_note_only": all(
                card.implementation_status == "note_only" for card in cards
            ),
            "all_proposals_review_required": all(
                proposal.review_required for proposal in proposals
            ),
            "card_count": len(cards),
            "families": families,
            "operator_count": operator_count,
            "proposal_count": len(proposals),
        },
        "safety": {
            "arbitrary_code_execution": False,
            "contains_private_traces": False,
            "modifies_estimator_scores": False,
            "publishes_private_candidates": False,
            "research_claim": False,
            "review_required_before_implementation": True,
        },
        "private_qwen_research_binding": PRIVATE_QWEN_RESEARCH_BINDING,
        "paper_cards": [_paper_card_entry(card) for card in cards],
        "hypothesis_proposals": [
            proposal.model_dump(mode="json") for proposal in proposals
        ],
    }


def write_deepevolve_research_hooks_manifest(
    out: Path = DEFAULT_MANIFEST_PATH,
    *,
    paper_card_dir: Path | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    manifest = build_deepevolve_research_hooks_manifest(
        paper_card_dir=paper_card_dir,
        root=project_root,
    )
    resolved_out = _resolve_path(out, project_root)
    resolved_out.parent.mkdir(parents=True, exist_ok=True)
    resolved_out.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def verify_deepevolve_research_hooks_manifest(
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    *,
    paper_card_dir: Path | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    resolved_manifest_path = _resolve_path(manifest_path, project_root)
    failures: list[str] = []
    try:
        manifest = json.loads(resolved_manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _verification_result(
            manifest_path=manifest_path,
            manifest={},
            failures=[f"Manifest could not be read as JSON: {exc}"],
        )

    expected = build_deepevolve_research_hooks_manifest(
        paper_card_dir=paper_card_dir,
        root=project_root,
    )
    if manifest != expected:
        failures.append("DeepEvolve research hook manifest is not in sync.")

    if manifest.get("schema_version") != DEEPEVOLVE_RESEARCH_HOOKS_SCHEMA:
        failures.append("Manifest schema_version is unexpected.")

    safety = manifest.get("safety")
    if not isinstance(safety, dict):
        failures.append("Manifest safety block is missing.")
    else:
        for flag in _REQUIRED_FALSE_SAFETY_FLAGS:
            if safety.get(flag) is not False:
                failures.append(f"safety.{flag} must be false.")
        if safety.get("review_required_before_implementation") is not True:
            failures.append(
                "safety.review_required_before_implementation must be true."
            )

    _validate_private_qwen_binding(
        manifest.get("private_qwen_research_binding"),
        failures=failures,
    )

    paper_cards = manifest.get("paper_cards")
    if not isinstance(paper_cards, list):
        failures.append("Manifest paper_cards must be a list.")
        paper_cards = []
    for index, card in enumerate(paper_cards):
        _validate_manifest_card(index=index, card=card, failures=failures)

    proposals = manifest.get("hypothesis_proposals")
    if not isinstance(proposals, list):
        failures.append("Manifest hypothesis_proposals must be a list.")
        proposals = []
    for index, proposal in enumerate(proposals):
        _validate_manifest_proposal(
            index=index,
            proposal=proposal,
            failures=failures,
        )

    summary = manifest.get("summary")
    if not isinstance(summary, dict):
        failures.append("Manifest summary block is missing.")
    else:
        _validate_summary(
            summary=summary,
            paper_cards=paper_cards,
            proposals=proposals,
            failures=failures,
        )

    return _verification_result(
        manifest_path=manifest_path,
        manifest=manifest,
        failures=failures,
    )


def _resolve_path(path: Path, root: Path) -> Path:
    if path.is_absolute():
        return path
    return root / path


def _validate_private_qwen_binding(
    binding: object,
    *,
    failures: list[str],
) -> None:
    if not isinstance(binding, dict):
        failures.append("private_qwen_research_binding must be a mapping.")
        return
    for key, expected_value in PRIVATE_QWEN_RESEARCH_BINDING.items():
        if binding.get(key) != expected_value:
            failures.append(f"private_qwen_research_binding.{key} is not synchronized.")

    proposal_gate = binding.get("proposal_gate")
    if not isinstance(proposal_gate, dict):
        failures.append(
            "private_qwen_research_binding.proposal_gate must be a mapping."
        )
    else:
        for key in (
            "attackplan_validation_required",
            "proof_obligation_generation_required",
            "estimator_compatibility_required",
            "human_review_required_before_claim",
        ):
            if proposal_gate.get(key) is not True:
                failures.append(f"private_qwen_research_binding.{key} must be true.")

    if binding.get("public_publication_allowed") is not False:
        failures.append("private_qwen_research_binding must not be public.")


def _paper_card_entry(card: PaperCard) -> dict[str, Any]:
    return {
        "authors": card.authors,
        "family": card.family,
        "implementation_status": card.implementation_status,
        "key_ideas": card.key_ideas,
        "operators_suggested": card.operators_suggested,
        "relevance": card.relevance,
        "risk": card.risk,
        "title": card.title,
        "url": card.url,
        "year": card.year,
    }


def _validate_manifest_card(
    *,
    index: int,
    card: object,
    failures: list[str],
) -> None:
    if not isinstance(card, dict):
        failures.append(f"paper_cards[{index}] must be a mapping.")
        return
    try:
        PaperCard.model_validate(card)
    except ValidationError as exc:
        failures.append(f"paper_cards[{index}] failed validation: {exc}")
        return
    if card.get("implementation_status") != "note_only":
        failures.append(
            f"paper_cards[{index}].implementation_status must be note_only."
        )
    operators = card.get("operators_suggested")
    if not isinstance(operators, list) or not set(operators) <= ALLOWED_OPERATORS:
        failures.append(f"paper_cards[{index}].operators_suggested is unsupported.")
    risk = card.get("risk")
    if not isinstance(risk, str) or "review" not in risk.lower():
        failures.append(f"paper_cards[{index}].risk must mention review.")


def _validate_manifest_proposal(
    *,
    index: int,
    proposal: object,
    failures: list[str],
) -> None:
    if not isinstance(proposal, dict):
        failures.append(f"hypothesis_proposals[{index}] must be a mapping.")
        return
    if proposal.get("review_required") is not True:
        failures.append(f"hypothesis_proposals[{index}].review_required must be true.")
    operator = proposal.get("operator")
    if operator not in ALLOWED_OPERATORS:
        failures.append(f"hypothesis_proposals[{index}].operator is unsupported.")
    if not proposal.get("source_papers"):
        failures.append(f"hypothesis_proposals[{index}].source_papers is empty.")


def _validate_summary(
    *,
    summary: dict[str, Any],
    paper_cards: list[object],
    proposals: list[object],
    failures: list[str],
) -> None:
    if summary.get("card_count") != len(paper_cards):
        failures.append("summary.card_count does not match paper_cards.")
    if summary.get("proposal_count") != len(proposals):
        failures.append("summary.proposal_count does not match hypothesis_proposals.")
    operator_count = sum(
        len(card.get("operators_suggested", []))
        for card in paper_cards
        if isinstance(card, dict)
    )
    if summary.get("operator_count") != operator_count:
        failures.append("summary.operator_count does not match paper_cards.")
    if summary.get("all_cards_note_only") is not True:
        failures.append("summary.all_cards_note_only must be true.")
    if summary.get("all_proposals_review_required") is not True:
        failures.append("summary.all_proposals_review_required must be true.")
    families = set(summary.get("families", []))
    if families < _REQUIRED_FAMILIES:
        missing = sorted(_REQUIRED_FAMILIES - families)
        failures.append(f"summary.families is missing: {', '.join(missing)}.")


def _verification_result(
    *,
    manifest_path: Path,
    manifest: dict[str, Any],
    failures: list[str],
) -> dict[str, Any]:
    summary = manifest.get("summary") if isinstance(manifest, dict) else {}
    if not isinstance(summary, dict):
        summary = {}
    return {
        "schema_version": DEEPEVOLVE_RESEARCH_HOOKS_VERIFICATION_SCHEMA,
        "manifest_path": manifest_path.as_posix(),
        "accepted": not failures,
        "summary": {
            "card_count": int(summary.get("card_count", 0) or 0),
            "failure_count": len(failures),
            "proposal_count": int(summary.get("proposal_count", 0) or 0),
            "private_qwen_bound": _private_qwen_bound(manifest),
        },
        "failures": failures,
    }


def _private_qwen_bound(manifest: dict[str, Any]) -> bool:
    return (
        manifest.get("private_qwen_research_binding") == PRIVATE_QWEN_RESEARCH_BINDING
    )


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()
