from pathlib import Path

from agades_pqc_gym.core.operators import ALLOWED_OPERATORS
from agades_pqc_gym.deepevolve_hooks.injection import (
    PAPER_CARD_INJECTION_BATCH_SCHEMA,
    build_paper_card_injection_batch,
    write_paper_card_injection_batch,
)
from agades_pqc_gym.deepevolve_hooks.operator_proposals import (
    proposals_from_paper_card,
)
from agades_pqc_gym.deepevolve_hooks.paper_card import load_paper_cards
from agades_pqc_gym.integrations.private_run_policy import build_private_run_policy


def test_paper_cards_cover_first_research_families() -> None:
    cards = load_paper_cards(Path("examples/paper_cards"))

    families = {card.family for card in cards}
    assert {
        "LWE",
        "MLWE",
        "CODE_BASED",
        "HASH_BASED",
        "IMPLEMENTATION_SECURITY",
        "ISOGENY_HISTORICAL",
        "MULTIVARIATE",
    } <= families

    for card in cards:
        assert card.implementation_status == "note_only"
        assert set(card.operators_suggested) <= ALLOWED_OPERATORS
        assert "review" in card.risk.lower()


def test_paper_cards_generate_review_gated_hypotheses() -> None:
    cards = load_paper_cards(Path("examples/paper_cards"))
    proposals = [
        proposal
        for card in cards
        for proposal in proposals_from_paper_card(card)
    ]

    assert proposals
    assert all(proposal.review_required for proposal in proposals)
    assert {proposal.target_family for proposal in proposals} >= {
        "CODE_BASED",
        "HASH_BASED",
        "IMPLEMENTATION_SECURITY",
        "ISOGENY_HISTORICAL",
        "MULTIVARIATE",
    }


def test_paper_cards_build_private_injection_batch() -> None:
    batch = build_paper_card_injection_batch(
        Path("examples/paper_cards"),
        run_id="paper-card-review",
    )

    assert batch["schema_version"] == PAPER_CARD_INJECTION_BATCH_SCHEMA
    assert batch["run_id"] == "paper-card-review"
    assert batch["source"]["input_format"] == "yaml_paper_cards"
    assert batch["summary"] == {
        "all_injections_review_required": True,
        "card_count": 8,
        "families": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "LWE",
            "MLWE",
            "MULTIVARIATE",
        ],
        "injection_count": 13,
        "operator_count": 13,
    }
    assert batch["safety"] == {
        "arbitrary_code_execution": False,
        "contains_private_traces": False,
        "modifies_estimator_scores": False,
        "publishes_private_candidates": False,
        "research_claim": False,
        "writes_attack_plans": False,
    }
    assert all(
        injection["review_required"] is True
        for injection in batch["injections"]
    )
    assert all(
        injection["public_release_ok"] is False
        for injection in batch["injections"]
    )
    assert all(
        "Do not implement, score, or publish" in injection["candidate_prompt"]
        for injection in batch["injections"]
    )


def test_paper_card_injection_writer_requires_private_output(
    tmp_path: Path,
) -> None:
    public_out = tmp_path / "docs" / "paper_card_injections.json"

    try:
        write_paper_card_injection_batch(
            public_out,
            paper_card_dir=Path("examples/paper_cards"),
            run_id="paper-card-review",
            policy=build_private_run_policy(),
            root=tmp_path,
        )
    except ValueError as exc:
        assert "forbidden public root" in str(exc)
    else:
        raise AssertionError("public paper-card injection output was accepted")
