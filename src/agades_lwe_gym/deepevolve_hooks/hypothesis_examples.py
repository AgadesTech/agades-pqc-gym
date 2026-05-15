from __future__ import annotations

from agades_lwe_gym.deepevolve_hooks.hypothesis import HypothesisProposal

MODULE_BKZ_COST_ADJUSTMENT_V0 = HypothesisProposal(
    hypothesis_id="module_bkz_cost_adjustment_v0",
    source_papers=["https://arxiv.org/abs/2510.10540"],
    target_family="MLWE",
    operator="module_lattice_reduction_hypothesis",
    claim=(
        "Module-aware BKZ may shift effective blocksize under specific "
        "number-field assumptions."
    ),
    implementation_plan=(
        "Represent as an assumption-tagged operator; do not use as final score "
        "until reviewed."
    ),
    review_required=True,
)

