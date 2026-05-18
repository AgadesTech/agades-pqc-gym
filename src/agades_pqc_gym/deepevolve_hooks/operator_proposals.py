from __future__ import annotations

from agades_pqc_gym.deepevolve_hooks.hypothesis import HypothesisProposal
from agades_pqc_gym.deepevolve_hooks.paper_card import PaperCard


def proposals_from_paper_card(card: PaperCard) -> list[HypothesisProposal]:
    proposals: list[HypothesisProposal] = []
    for operator in card.operators_suggested:
        proposals.append(
            HypothesisProposal(
                hypothesis_id=f"{operator}_from_{card.year}",
                source_papers=[card.url],
                target_family=card.family,
                operator=operator,
                claim=card.relevance,
                implementation_plan=(
                    "Represent as an assumption-tagged operator until expert review "
                    "and independent validation are complete."
                ),
                review_required=True,
            )
        )
    return proposals

