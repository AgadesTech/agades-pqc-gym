from __future__ import annotations

import math

from agades_pqc_gym.core.attack_plan import AttackOperator, AttackPlan
from agades_pqc_gym.evaluators.base import EstimatorResult

TOY_PREIMAGE_BOUND_MODEL = "toy_preimage_bound"
TOY_PREIMAGE_ASSUMPTION = "toy_hash_preimage_bound_model"
TOY_COLLISION_BOUND_MODEL = "toy_collision_bound"
TOY_COLLISION_ASSUMPTION = "toy_hash_collision_bound_model"
TOY_SIGNATURE_CHAIN_MODEL = "toy_wots_chain_verify"
TOY_SIGNATURE_CHAIN_ASSUMPTION = "toy_hash_signature_chain_model"
TOY_MERKLE_AUTH_PATH_MODEL = "toy_merkle_auth_path_verify"
TOY_MERKLE_AUTH_PATH_ASSUMPTION = "toy_hash_merkle_auth_path_model"
TOY_FORS_AUTH_PATH_MODEL = "toy_fors_auth_path_verify"
TOY_FORS_AUTH_PATH_ASSUMPTION = "toy_hash_fors_auth_path_model"
TOY_SLH_DSA_HYPERTREE_MODEL = "toy_slh_dsa_hypertree_verify"
TOY_SLH_DSA_HYPERTREE_ASSUMPTION = "toy_hash_slh_dsa_hypertree_model"
TOY_HASH_REUSED_SALT_MODEL = "toy_hash_reused_salt"
TOY_HASH_MISUSE_ASSUMPTION = "toy_hash_misuse_fixture_model"


class ToyHashBoundEstimator:
    """Toy hash-bound evaluator for public verifier plumbing."""

    estimator_name = "toy-hash-bound-estimator"
    estimator_version = "0.1.0"

    def estimate(self, plan: AttackPlan) -> EstimatorResult:
        operator = _bound_operator(plan)
        if operator.type == "misuse_check":
            return _estimate_reused_salt_misuse(plan, operator)
        if operator.type == "hash_signature_verification":
            if operator.params.get("signature_model") == TOY_MERKLE_AUTH_PATH_MODEL:
                return _estimate_merkle_auth_path(plan, operator)
            if operator.params.get("signature_model") == TOY_FORS_AUTH_PATH_MODEL:
                return _estimate_fors_auth_path(plan, operator)
            if (
                operator.params.get("signature_model")
                == TOY_SLH_DSA_HYPERTREE_MODEL
            ):
                return _estimate_slh_dsa_hypertree(plan, operator)
            return _estimate_signature_chain(plan, operator)
        if operator.params["bound_model"] == TOY_COLLISION_BOUND_MODEL:
            return _estimate_collision_bound(plan, operator)

        digest_bits = _required_int(plan.target.n, "n")
        classical_preimage_bits = float(digest_bits)
        toy_collision_bits = digest_bits / 2.0

        return EstimatorResult(
            estimator_name=self.estimator_name,
            estimator_version=self.estimator_version,
            estimator_commit=None,
            evaluation_status="ok",
            attack_type=f"{operator.type}:{operator.params['bound_model']}",
            time_bits=round(classical_preimage_bits, 4),
            memory_bits=1.0,
            success_probability=None,
            raw_output={
                "bound_model": TOY_PREIMAGE_BOUND_MODEL,
                "classical_preimage_bits": round(classical_preimage_bits, 4),
                "digest_bits": digest_bits,
                "toy_collision_bits": round(toy_collision_bits, 4),
            },
            warnings=[
                "Toy hash-bound output is for public evaluator plumbing only; "
                "it is not a security claim."
            ],
        )


def _estimate_collision_bound(
    plan: AttackPlan,
    operator: AttackOperator,
) -> EstimatorResult:
    digest_bits = _required_int(plan.target.n, "n")
    birthday_collision_bits = digest_bits / 2.0

    return EstimatorResult(
        estimator_name=ToyHashBoundEstimator.estimator_name,
        estimator_version=ToyHashBoundEstimator.estimator_version,
        estimator_commit=None,
        evaluation_status="ok",
        attack_type=f"{operator.type}:{operator.params['bound_model']}",
        time_bits=round(birthday_collision_bits, 4),
        memory_bits=round(birthday_collision_bits, 4),
        success_probability=None,
        raw_output={
            "bound_model": TOY_COLLISION_BOUND_MODEL,
            "birthday_collision_bits": round(birthday_collision_bits, 4),
            "digest_bits": digest_bits,
            "hash_function": plan.target.hash_function,
        },
        warnings=[
            "Toy hash collision-bound output is for public evaluator plumbing "
            "only; it is not a security claim."
        ],
    )


def _bound_operator(plan: AttackPlan) -> AttackOperator:
    for operator in plan.operators:
        if operator.type in {
            "security_bound_check",
            "hash_signature_verification",
            "misuse_check",
        }:
            return operator
    raise ValueError(
        "HASH_BASED estimate requires security_bound_check or "
        "hash_signature_verification or misuse_check"
    )


def _estimate_reused_salt_misuse(
    plan: AttackPlan,
    operator: AttackOperator,
) -> EstimatorResult:
    fixture = operator.params["fixture"]
    if fixture != TOY_HASH_REUSED_SALT_MODEL:
        raise ValueError(f"unsupported HASH_BASED misuse_check fixture: {fixture}")
    record_count = _required_int(operator.params.get("record_count"), "record_count")
    expected_reuse_groups = _required_int(
        operator.params.get("expected_reuse_groups"),
        "expected_reuse_groups",
    )
    salt_bytes = _required_int(operator.params.get("salt_bytes"), "salt_bytes")
    pair_checks = math.comb(record_count, 2)

    return EstimatorResult(
        estimator_name=ToyHashBoundEstimator.estimator_name,
        estimator_version=ToyHashBoundEstimator.estimator_version,
        estimator_commit=None,
        evaluation_status="ok",
        attack_type=f"{operator.type}:{fixture}",
        time_bits=round(math.log2(max(1, pair_checks)), 4),
        memory_bits=round(math.log2(max(1, record_count * salt_bytes)), 4),
        success_probability=None,
        raw_output={
            "expected_reuse_groups": expected_reuse_groups,
            "fixture": TOY_HASH_REUSED_SALT_MODEL,
            "hash_function": plan.target.hash_function,
            "model": "toy_hash_reused_salt_misuse_check",
            "pair_checks": pair_checks,
            "record_count": record_count,
            "salt_bytes": salt_bytes,
        },
        warnings=[
            "Toy hash misuse output is for public evaluator plumbing only; "
            "it is not a security claim."
        ],
    )


def _estimate_signature_chain(
    plan: AttackPlan,
    operator: AttackOperator,
) -> EstimatorResult:
    digest_bits = _required_int(plan.target.n, "n")
    chain_count = _required_int(operator.params.get("chain_count"), "chain_count")
    max_chain_steps = _required_int(
        operator.params.get("max_chain_steps"),
        "max_chain_steps",
    )
    toy_chain_hashes = chain_count * max_chain_steps
    memory_bytes = chain_count * (digest_bits // 8)

    return EstimatorResult(
        estimator_name=ToyHashBoundEstimator.estimator_name,
        estimator_version=ToyHashBoundEstimator.estimator_version,
        estimator_commit=None,
        evaluation_status="ok",
        attack_type=f"{operator.type}:{operator.params['signature_model']}",
        time_bits=round(math.log2(toy_chain_hashes), 4),
        memory_bits=round(math.log2(memory_bytes), 4),
        success_probability=None,
        raw_output={
            "chain_count": chain_count,
            "digest_bits": digest_bits,
            "hash_function": plan.target.hash_function,
            "max_chain_steps": max_chain_steps,
            "model": TOY_SIGNATURE_CHAIN_MODEL,
            "toy_chain_hashes": toy_chain_hashes,
        },
        warnings=[
            "Toy hash-signature chain output is for public evaluator plumbing "
            "only; it is not a security claim."
        ],
    )


def _estimate_merkle_auth_path(
    plan: AttackPlan,
    operator: AttackOperator,
) -> EstimatorResult:
    digest_bits = _required_int(plan.target.n, "n")
    tree_height = _required_int(operator.params.get("tree_height"), "tree_height")
    leaf_index = _required_int(operator.params.get("leaf_index"), "leaf_index")
    toy_auth_path_hashes = tree_height + 1
    memory_bytes = toy_auth_path_hashes * (digest_bits // 8)

    return EstimatorResult(
        estimator_name=ToyHashBoundEstimator.estimator_name,
        estimator_version=ToyHashBoundEstimator.estimator_version,
        estimator_commit=None,
        evaluation_status="ok",
        attack_type=f"{operator.type}:{operator.params['signature_model']}",
        time_bits=round(math.log2(toy_auth_path_hashes), 4),
        memory_bits=round(math.log2(memory_bytes), 4),
        success_probability=None,
        raw_output={
            "digest_bits": digest_bits,
            "hash_function": plan.target.hash_function,
            "leaf_index": leaf_index,
            "model": TOY_MERKLE_AUTH_PATH_MODEL,
            "tree_height": tree_height,
            "toy_auth_path_hashes": toy_auth_path_hashes,
        },
        warnings=[
            "Toy Merkle auth-path output is for public evaluator plumbing "
            "only; it is not a signature security claim and not a security "
            "claim."
        ],
    )


def _estimate_fors_auth_path(
    plan: AttackPlan,
    operator: AttackOperator,
) -> EstimatorResult:
    digest_bits = _required_int(plan.target.n, "n")
    tree_count = _required_int(operator.params.get("tree_count"), "tree_count")
    tree_height = _required_int(operator.params.get("tree_height"), "tree_height")
    selected_indices = _required_int_list(
        operator.params.get("selected_indices"),
        "selected_indices",
    )
    toy_fors_hashes = tree_count * (tree_height + 1)
    memory_bytes = toy_fors_hashes * (digest_bits // 8)

    return EstimatorResult(
        estimator_name=ToyHashBoundEstimator.estimator_name,
        estimator_version=ToyHashBoundEstimator.estimator_version,
        estimator_commit=None,
        evaluation_status="ok",
        attack_type=f"{operator.type}:{operator.params['signature_model']}",
        time_bits=round(math.log2(toy_fors_hashes), 4),
        memory_bits=round(math.log2(memory_bytes), 4),
        success_probability=None,
        raw_output={
            "digest_bits": digest_bits,
            "hash_function": plan.target.hash_function,
            "model": TOY_FORS_AUTH_PATH_MODEL,
            "selected_indices": selected_indices,
            "tree_count": tree_count,
            "tree_height": tree_height,
            "toy_fors_hashes": toy_fors_hashes,
        },
        warnings=[
            "Toy FORS auth-path output is for public evaluator plumbing only; "
            "it is not an SLH-DSA result and not a security claim."
        ],
    )


def _estimate_slh_dsa_hypertree(
    plan: AttackPlan,
    operator: AttackOperator,
) -> EstimatorResult:
    digest_bits = _required_int(plan.target.n, "n")
    fors_tree_count = _required_int(
        operator.params.get("fors_tree_count"),
        "fors_tree_count",
    )
    fors_tree_height = _required_int(
        operator.params.get("fors_tree_height"),
        "fors_tree_height",
    )
    fors_selected_indices = _required_int_list(
        operator.params.get("fors_selected_indices"),
        "fors_selected_indices",
    )
    wots_chain_count = _required_int(
        operator.params.get("wots_chain_count"),
        "wots_chain_count",
    )
    wots_max_chain_steps = _required_int(
        operator.params.get("wots_max_chain_steps"),
        "wots_max_chain_steps",
    )
    hypertree_height = _required_int(
        operator.params.get("hypertree_height"),
        "hypertree_height",
    )
    hypertree_leaf_index = _required_int(
        operator.params.get("hypertree_leaf_index"),
        "hypertree_leaf_index",
    )
    toy_signature_hashes = (
        fors_tree_count * (fors_tree_height + 1)
        + wots_chain_count * wots_max_chain_steps
        + hypertree_height
        + 2
    )
    memory_bytes = toy_signature_hashes * (digest_bits // 8)

    return EstimatorResult(
        estimator_name=ToyHashBoundEstimator.estimator_name,
        estimator_version=ToyHashBoundEstimator.estimator_version,
        estimator_commit=None,
        evaluation_status="ok",
        attack_type=f"{operator.type}:{operator.params['signature_model']}",
        time_bits=round(math.log2(toy_signature_hashes), 4),
        memory_bits=round(math.log2(memory_bytes), 4),
        success_probability=None,
        raw_output={
            "digest_bits": digest_bits,
            "fors_selected_indices": fors_selected_indices,
            "fors_tree_count": fors_tree_count,
            "fors_tree_height": fors_tree_height,
            "hash_function": plan.target.hash_function,
            "hypertree_height": hypertree_height,
            "hypertree_leaf_index": hypertree_leaf_index,
            "model": TOY_SLH_DSA_HYPERTREE_MODEL,
            "toy_signature_hashes": toy_signature_hashes,
            "wots_chain_count": wots_chain_count,
            "wots_max_chain_steps": wots_max_chain_steps,
        },
        warnings=[
            "Toy SLH-DSA-like hypertree output is for public evaluator "
            "plumbing only; it is not an SLH-DSA result and not a security "
            "claim."
        ],
    )


def _required_int(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"HASH_BASED target requires {name}")
    return value


def _required_int_list(value: object, name: str) -> list[int]:
    if not isinstance(value, list) or any(
        not isinstance(item, int) or isinstance(item, bool) for item in value
    ):
        raise ValueError(f"HASH_BASED target requires integer list {name}")
    return value
