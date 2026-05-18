from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agades_pqc_gym.deepevolve_hooks.operator_proposals import (
    proposals_from_paper_card,
)
from agades_pqc_gym.deepevolve_hooks.paper_card import load_paper_cards
from agades_pqc_gym.evolution.scheduler import validate_policy_private_path

PAPER_CARD_INJECTION_BATCH_SCHEMA = "agades.pqc.paper_card_injection_batch.v1"
ROOT = Path(__file__).resolve().parents[3]


class PaperCardInjection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    injection_id: str
    hypothesis_id: str
    source_papers: list[str] = Field(min_length=1)
    source_title: str
    target_family: str
    operator: str
    claim: str
    implementation_plan: str
    candidate_prompt: str
    review_required: bool = True
    public_release_ok: bool = False
    redaction_reason: str = "private literature-derived hypothesis queue"
    injection_stage: str = "paper_card_review"
    execution_safety: dict[str, bool]


class PaperCardInjectionBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str
    run_id: str
    source: dict[str, Any]
    summary: dict[str, Any]
    safety: dict[str, bool]
    injections: list[PaperCardInjection]


def build_paper_card_injection_batch(
    paper_card_dir: Path | None = None,
    *,
    run_id: str = "paper-card-injection",
) -> dict[str, Any]:
    if not run_id.strip():
        raise ValueError("paper-card injection run_id must be non-empty")
    source_dir = (paper_card_dir or ROOT / "examples" / "paper_cards").resolve()
    cards = load_paper_cards(source_dir)
    injections: list[PaperCardInjection] = []
    for card in cards:
        if card.implementation_status != "note_only":
            raise ValueError(
                "paper-card injections require note_only source cards: "
                f"{card.title}"
            )
        for proposal in proposals_from_paper_card(card):
            if proposal.review_required is not True:
                raise ValueError(
                    "paper-card injections require review-gated proposals: "
                    f"{proposal.hypothesis_id}"
                )
            injections.append(
                PaperCardInjection(
                    injection_id=_injection_id(
                        title=card.title,
                        hypothesis_id=proposal.hypothesis_id,
                    ),
                    hypothesis_id=proposal.hypothesis_id,
                    source_papers=proposal.source_papers,
                    source_title=card.title,
                    target_family=proposal.target_family,
                    operator=proposal.operator,
                    claim=proposal.claim,
                    implementation_plan=proposal.implementation_plan,
                    candidate_prompt=_candidate_prompt(
                        source_title=card.title,
                        target_family=proposal.target_family,
                        operator=proposal.operator,
                        claim=proposal.claim,
                        implementation_plan=proposal.implementation_plan,
                    ),
                    execution_safety={
                        "arbitrary_code_execution": False,
                        "modifies_estimator_scores": False,
                        "publishes_private_candidates": False,
                        "writes_attack_plans": False,
                    },
                )
            )

    if not injections:
        raise ValueError("paper-card injection batch must contain at least one item")

    families = sorted({card.family for card in cards})
    operator_count = sum(len(card.operators_suggested) for card in cards)
    batch = PaperCardInjectionBatch(
        schema_version=PAPER_CARD_INJECTION_BATCH_SCHEMA,
        run_id=run_id,
        source={
            "paper_card_directory": _display_path(source_dir),
            "input_format": "yaml_paper_cards",
        },
        summary={
            "all_injections_review_required": all(
                injection.review_required for injection in injections
            ),
            "card_count": len(cards),
            "families": families,
            "injection_count": len(injections),
            "operator_count": operator_count,
        },
        safety={
            "arbitrary_code_execution": False,
            "contains_private_traces": False,
            "modifies_estimator_scores": False,
            "publishes_private_candidates": False,
            "research_claim": False,
            "writes_attack_plans": False,
        },
        injections=injections,
    )
    return batch.model_dump(mode="json")


def write_paper_card_injection_batch(
    out: Path,
    *,
    paper_card_dir: Path | None = None,
    run_id: str = "paper-card-injection",
    policy: dict[str, Any],
    root: Path | None = None,
) -> dict[str, Any]:
    validate_policy_private_path(out, policy=policy, root=root or ROOT)
    batch = build_paper_card_injection_batch(
        paper_card_dir,
        run_id=run_id,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(batch, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return batch


def _candidate_prompt(
    *,
    source_title: str,
    target_family: str,
    operator: str,
    claim: str,
    implementation_plan: str,
) -> str:
    return (
        "Do not implement, score, or publish this hypothesis before expert "
        f"review. Source card: {source_title}. Target family: {target_family}. "
        f"Operator: {operator}. Hypothesis: {claim}. Review-only plan: "
        f"{implementation_plan}"
    )


def _injection_id(*, title: str, hypothesis_id: str) -> str:
    return f"{_slug(title)}__{_slug(hypothesis_id)}"


def _slug(value: str) -> str:
    chars: list[str] = []
    previous_sep = False
    for char in value.lower():
        if char.isalnum():
            chars.append(char)
            previous_sep = False
        elif not previous_sep:
            chars.append("_")
            previous_sep = True
    return "".join(chars).strip("_")


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()
