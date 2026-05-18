from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_SIGNATURE_CHAIN_COUNT = 16
MAX_SIGNATURE_CHAIN_STEPS = 64
MAX_MERKLE_TREE_HEIGHT = 16
MAX_FORS_TREE_COUNT = 16
MAX_FORS_TREE_HEIGHT = 16
_CHAIN_DOMAIN = b"agades-pqc-toy-wots-chain-v1:"
_MERKLE_NODE_DOMAIN = b"agades-pqc-toy-merkle-node-v1:"
_FORS_NODE_DOMAIN = b"agades-pqc-toy-fors-node-v1:"
_SLH_DSA_FORS_AGGREGATE_DOMAIN = (
    b"agades-pqc-toy-slh-dsa-fors-aggregate-v1:"
)
_SLH_DSA_HYPERTREE_LEAF_DOMAIN = (
    b"agades-pqc-toy-slh-dsa-hypertree-leaf-v1:"
)


class ToyHashSignatureChainFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["agades.pqc.hash_based_toy_signature_chain.v1"]
    family: Literal["HASH_BASED"]
    target_name: str = Field(min_length=1)
    digest_bits: int = Field(gt=0, le=64)
    hash_function: Literal["SHAKE256"]
    signature_model: Literal["toy_wots_chain_verify"]
    chain_count: int = Field(gt=0, le=MAX_SIGNATURE_CHAIN_COUNT)
    max_chain_steps: int = Field(gt=0, le=MAX_SIGNATURE_CHAIN_STEPS)
    signature_nodes_hex: list[str] = Field(min_length=1)
    remaining_steps: list[int] = Field(min_length=1)
    public_key_roots_hex: list[str] = Field(min_length=1)
    public: Literal[True]
    security_claim: Literal[False]

    @field_validator("signature_nodes_hex", "public_key_roots_hex")
    @classmethod
    def hashes_must_be_lowercase_hex(cls, values: list[str]) -> list[str]:
        for value in values:
            if value != value.lower():
                raise ValueError("hash values must be lowercase")
            try:
                bytes.fromhex(value)
            except ValueError as exc:
                raise ValueError("hash values must be valid hexadecimal") from exc
        return values

    @model_validator(mode="after")
    def validate_chain_shape(self) -> ToyHashSignatureChainFixture:
        if self.digest_bits % 8 != 0:
            raise ValueError("digest_bits must be byte-aligned")
        expected_hex_length = self.digest_bits // 4
        if len(self.signature_nodes_hex) != self.chain_count:
            raise ValueError("signature_nodes_hex length must match chain_count")
        if len(self.remaining_steps) != self.chain_count:
            raise ValueError("remaining_steps length must match chain_count")
        if len(self.public_key_roots_hex) != self.chain_count:
            raise ValueError("public_key_roots_hex length must match chain_count")
        for value in [*self.signature_nodes_hex, *self.public_key_roots_hex]:
            if len(value) != expected_hex_length:
                raise ValueError("chain hash length must match digest_bits")
        for steps in self.remaining_steps:
            if steps < 0 or steps > self.max_chain_steps:
                raise ValueError("remaining_steps must be within max_chain_steps")
        return self


class ToyHashSignatureChainResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verified: bool
    target_name: str
    digest_bits: int
    hash_function: str
    signature_model: str
    chain_count: int
    max_chain_steps: int
    verified_chains: int
    public: bool
    security_claim: bool


class ToyHashMerkleAuthPathFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["agades.pqc.hash_based_toy_merkle_auth_path.v1"]
    family: Literal["HASH_BASED"]
    target_name: str = Field(min_length=1)
    digest_bits: int = Field(gt=0, le=64)
    hash_function: Literal["SHAKE256"]
    signature_model: Literal["toy_merkle_auth_path_verify"]
    tree_height: int = Field(gt=0, le=MAX_MERKLE_TREE_HEIGHT)
    leaf_index: int = Field(ge=0)
    leaf_hex: str
    auth_path_hex: list[str] = Field(min_length=1)
    root_hex: str
    public: Literal[True]
    security_claim: Literal[False]

    @field_validator("leaf_hex", "root_hex")
    @classmethod
    def hash_must_be_lowercase_hex(cls, value: str) -> str:
        _validate_lowercase_hex(value)
        return value

    @field_validator("auth_path_hex")
    @classmethod
    def path_must_be_lowercase_hex(cls, values: list[str]) -> list[str]:
        for value in values:
            _validate_lowercase_hex(value)
        return values

    @model_validator(mode="after")
    def validate_merkle_shape(self) -> ToyHashMerkleAuthPathFixture:
        if self.digest_bits % 8 != 0:
            raise ValueError("digest_bits must be byte-aligned")
        if self.leaf_index >= 2**self.tree_height:
            raise ValueError("leaf_index must be within tree height")
        if len(self.auth_path_hex) != self.tree_height:
            raise ValueError("auth_path_hex length must match tree_height")
        expected_hex_length = self.digest_bits // 4
        for value in [self.leaf_hex, self.root_hex, *self.auth_path_hex]:
            if len(value) != expected_hex_length:
                raise ValueError("Merkle node hash length must match digest_bits")
        return self


class ToyHashMerkleAuthPathResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verified: bool
    target_name: str
    digest_bits: int
    hash_function: str
    signature_model: str
    tree_height: int
    leaf_index: int
    public: bool
    security_claim: bool


class ToyHashForsAuthPathFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["agades.pqc.hash_based_toy_fors_auth_path.v1"]
    family: Literal["HASH_BASED"]
    target_name: str = Field(min_length=1)
    digest_bits: int = Field(gt=0, le=64)
    hash_function: Literal["SHAKE256"]
    signature_model: Literal["toy_fors_auth_path_verify"]
    tree_count: int = Field(gt=0, le=MAX_FORS_TREE_COUNT)
    tree_height: int = Field(gt=0, le=MAX_FORS_TREE_HEIGHT)
    selected_indices: list[int] = Field(min_length=1)
    leaves_hex: list[str] = Field(min_length=1)
    auth_paths_hex: list[list[str]] = Field(min_length=1)
    roots_hex: list[str] = Field(min_length=1)
    public: Literal[True]
    security_claim: Literal[False]

    @field_validator("leaves_hex", "roots_hex")
    @classmethod
    def fors_hashes_must_be_lowercase_hex(cls, values: list[str]) -> list[str]:
        for value in values:
            _validate_lowercase_hex(value)
        return values

    @field_validator("auth_paths_hex")
    @classmethod
    def fors_paths_must_be_lowercase_hex(
        cls,
        values: list[list[str]],
    ) -> list[list[str]]:
        for path in values:
            for value in path:
                _validate_lowercase_hex(value)
        return values

    @model_validator(mode="after")
    def validate_fors_shape(self) -> ToyHashForsAuthPathFixture:
        if self.digest_bits % 8 != 0:
            raise ValueError("digest_bits must be byte-aligned")
        if len(self.selected_indices) != self.tree_count:
            raise ValueError("selected_indices length must match tree_count")
        if len(self.leaves_hex) != self.tree_count:
            raise ValueError("leaves_hex length must match tree_count")
        if len(self.auth_paths_hex) != self.tree_count:
            raise ValueError("auth_paths_hex length must match tree_count")
        if len(self.roots_hex) != self.tree_count:
            raise ValueError("roots_hex length must match tree_count")
        expected_hex_length = self.digest_bits // 4
        for value in [*self.leaves_hex, *self.roots_hex]:
            if len(value) != expected_hex_length:
                raise ValueError("FORS node hash length must match digest_bits")
        for tree_index, selected_index in enumerate(self.selected_indices):
            if selected_index < 0 or selected_index >= 2**self.tree_height:
                raise ValueError("selected_indices must be within tree height")
            auth_path = self.auth_paths_hex[tree_index]
            if len(auth_path) != self.tree_height:
                raise ValueError("each FORS auth path length must match tree_height")
            for value in auth_path:
                if len(value) != expected_hex_length:
                    raise ValueError(
                        "FORS auth path hash length must match digest_bits"
                    )
        return self


class ToyHashForsAuthPathResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verified: bool
    target_name: str
    digest_bits: int
    hash_function: str
    signature_model: str
    tree_count: int
    tree_height: int
    selected_indices: list[int]
    verified_trees: int
    public: bool
    security_claim: bool


class ToyHashSlhDsaHypertreeFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["agades.pqc.hash_based_toy_slh_dsa_hypertree.v1"]
    family: Literal["HASH_BASED"]
    target_name: str = Field(min_length=1)
    digest_bits: int = Field(gt=0, le=64)
    hash_function: Literal["SHAKE256"]
    signature_model: Literal["toy_slh_dsa_hypertree_verify"]
    fors_tree_count: int = Field(gt=0, le=MAX_FORS_TREE_COUNT)
    fors_tree_height: int = Field(gt=0, le=MAX_FORS_TREE_HEIGHT)
    fors_selected_indices: list[int] = Field(min_length=1)
    fors_leaves_hex: list[str] = Field(min_length=1)
    fors_auth_paths_hex: list[list[str]] = Field(min_length=1)
    fors_roots_hex: list[str] = Field(min_length=1)
    wots_chain_count: int = Field(gt=0, le=MAX_SIGNATURE_CHAIN_COUNT)
    wots_max_chain_steps: int = Field(gt=0, le=MAX_SIGNATURE_CHAIN_STEPS)
    wots_signature_nodes_hex: list[str] = Field(min_length=1)
    wots_remaining_steps: list[int] = Field(min_length=1)
    wots_public_key_roots_hex: list[str] = Field(min_length=1)
    hypertree_height: int = Field(gt=0, le=MAX_MERKLE_TREE_HEIGHT)
    hypertree_leaf_index: int = Field(ge=0)
    hypertree_auth_path_hex: list[str] = Field(min_length=1)
    hypertree_root_hex: str
    public: Literal[True]
    security_claim: Literal[False]

    @field_validator(
        "fors_leaves_hex",
        "fors_roots_hex",
        "wots_signature_nodes_hex",
        "wots_public_key_roots_hex",
    )
    @classmethod
    def slh_hashes_must_be_lowercase_hex(cls, values: list[str]) -> list[str]:
        for value in values:
            _validate_lowercase_hex(value)
        return values

    @field_validator("fors_auth_paths_hex")
    @classmethod
    def slh_fors_paths_must_be_lowercase_hex(
        cls,
        values: list[list[str]],
    ) -> list[list[str]]:
        for path in values:
            for value in path:
                _validate_lowercase_hex(value)
        return values

    @field_validator("hypertree_auth_path_hex")
    @classmethod
    def slh_hypertree_path_must_be_lowercase_hex(
        cls,
        values: list[str],
    ) -> list[str]:
        for value in values:
            _validate_lowercase_hex(value)
        return values

    @field_validator("hypertree_root_hex")
    @classmethod
    def slh_root_must_be_lowercase_hex(cls, value: str) -> str:
        _validate_lowercase_hex(value)
        return value

    @model_validator(mode="after")
    def validate_slh_shape(self) -> ToyHashSlhDsaHypertreeFixture:
        if self.digest_bits % 8 != 0:
            raise ValueError("digest_bits must be byte-aligned")
        expected_hex_length = self.digest_bits // 4
        if len(self.fors_selected_indices) != self.fors_tree_count:
            raise ValueError("fors_selected_indices length must match tree_count")
        if len(self.fors_leaves_hex) != self.fors_tree_count:
            raise ValueError("fors_leaves_hex length must match tree_count")
        if len(self.fors_auth_paths_hex) != self.fors_tree_count:
            raise ValueError("fors_auth_paths_hex length must match tree_count")
        if len(self.fors_roots_hex) != self.fors_tree_count:
            raise ValueError("fors_roots_hex length must match tree_count")
        if len(self.wots_signature_nodes_hex) != self.wots_chain_count:
            raise ValueError(
                "wots_signature_nodes_hex length must match wots_chain_count"
            )
        if len(self.wots_remaining_steps) != self.wots_chain_count:
            raise ValueError(
                "wots_remaining_steps length must match wots_chain_count"
            )
        if len(self.wots_public_key_roots_hex) != self.wots_chain_count:
            raise ValueError(
                "wots_public_key_roots_hex length must match wots_chain_count"
            )
        if self.hypertree_leaf_index >= 2**self.hypertree_height:
            raise ValueError("hypertree_leaf_index must be within tree height")
        if len(self.hypertree_auth_path_hex) != self.hypertree_height:
            raise ValueError("hypertree_auth_path_hex length must match height")

        for value in [
            *self.fors_leaves_hex,
            *self.fors_roots_hex,
            *self.wots_signature_nodes_hex,
            *self.wots_public_key_roots_hex,
            *self.hypertree_auth_path_hex,
            self.hypertree_root_hex,
        ]:
            if len(value) != expected_hex_length:
                raise ValueError("SLH-DSA toy hash length must match digest_bits")

        for tree_index, selected_index in enumerate(self.fors_selected_indices):
            if selected_index < 0 or selected_index >= 2**self.fors_tree_height:
                raise ValueError("fors_selected_indices must be within tree height")
            auth_path = self.fors_auth_paths_hex[tree_index]
            if len(auth_path) != self.fors_tree_height:
                raise ValueError("each FORS auth path length must match height")
            for value in auth_path:
                if len(value) != expected_hex_length:
                    raise ValueError(
                        "FORS auth path hash length must match digest_bits"
                    )
        for steps in self.wots_remaining_steps:
            if steps < 0 or steps > self.wots_max_chain_steps:
                raise ValueError(
                    "wots_remaining_steps must be within wots_max_chain_steps"
                )
        return self


class ToyHashSlhDsaHypertreeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verified: bool
    target_name: str
    digest_bits: int
    hash_function: str
    signature_model: str
    fors_tree_count: int
    fors_tree_height: int
    fors_selected_indices: list[int]
    verified_fors_trees: int
    wots_chain_count: int
    wots_max_chain_steps: int
    verified_wots_chains: int
    hypertree_height: int
    hypertree_leaf_index: int
    public: bool
    security_claim: bool


def verify_toy_signature_chain_fixture(
    path: Path,
) -> ToyHashSignatureChainResult:
    fixture = ToyHashSignatureChainFixture.model_validate_json(
        path.read_text(encoding="utf-8")
    )

    verified_chains = 0
    for chain_index, node_hex in enumerate(fixture.signature_nodes_hex):
        node = bytes.fromhex(node_hex)
        for step_index in range(fixture.remaining_steps[chain_index]):
            node = _chain_step(
                node=node,
                chain_index=chain_index,
                step_index=step_index,
                digest_bytes=fixture.digest_bits // 8,
            )
        if node.hex() == fixture.public_key_roots_hex[chain_index]:
            verified_chains += 1

    return ToyHashSignatureChainResult(
        verified=verified_chains == fixture.chain_count,
        target_name=fixture.target_name,
        digest_bits=fixture.digest_bits,
        hash_function=fixture.hash_function,
        signature_model=fixture.signature_model,
        chain_count=fixture.chain_count,
        max_chain_steps=fixture.max_chain_steps,
        verified_chains=verified_chains,
        public=fixture.public,
        security_claim=fixture.security_claim,
    )


def verify_toy_merkle_auth_path_fixture(path: Path) -> ToyHashMerkleAuthPathResult:
    fixture = ToyHashMerkleAuthPathFixture.model_validate_json(
        path.read_text(encoding="utf-8")
    )

    node = bytes.fromhex(fixture.leaf_hex)
    index = fixture.leaf_index
    digest_bytes = fixture.digest_bits // 8
    for level, sibling_hex in enumerate(fixture.auth_path_hex):
        sibling = bytes.fromhex(sibling_hex)
        if index & 1:
            left, right = sibling, node
        else:
            left, right = node, sibling
        node = _merkle_parent(
            left=left,
            right=right,
            level=level,
            digest_bytes=digest_bytes,
        )
        index >>= 1

    return ToyHashMerkleAuthPathResult(
        verified=node.hex() == fixture.root_hex,
        target_name=fixture.target_name,
        digest_bits=fixture.digest_bits,
        hash_function=fixture.hash_function,
        signature_model=fixture.signature_model,
        tree_height=fixture.tree_height,
        leaf_index=fixture.leaf_index,
        public=fixture.public,
        security_claim=fixture.security_claim,
    )


def verify_toy_fors_auth_path_fixture(path: Path) -> ToyHashForsAuthPathResult:
    fixture = ToyHashForsAuthPathFixture.model_validate_json(
        path.read_text(encoding="utf-8")
    )

    digest_bytes = fixture.digest_bits // 8
    verified_trees = 0
    for tree_index, leaf_hex in enumerate(fixture.leaves_hex):
        node = bytes.fromhex(leaf_hex)
        index = fixture.selected_indices[tree_index]
        for level, sibling_hex in enumerate(fixture.auth_paths_hex[tree_index]):
            sibling = bytes.fromhex(sibling_hex)
            if index & 1:
                left, right = sibling, node
            else:
                left, right = node, sibling
            node = _fors_parent(
                tree_index=tree_index,
                level=level,
                left=left,
                right=right,
                digest_bytes=digest_bytes,
            )
            index >>= 1
        if node.hex() == fixture.roots_hex[tree_index]:
            verified_trees += 1

    return ToyHashForsAuthPathResult(
        verified=verified_trees == fixture.tree_count,
        target_name=fixture.target_name,
        digest_bits=fixture.digest_bits,
        hash_function=fixture.hash_function,
        signature_model=fixture.signature_model,
        tree_count=fixture.tree_count,
        tree_height=fixture.tree_height,
        selected_indices=fixture.selected_indices,
        verified_trees=verified_trees,
        public=fixture.public,
        security_claim=fixture.security_claim,
    )


def verify_toy_slh_dsa_hypertree_fixture(
    path: Path,
) -> ToyHashSlhDsaHypertreeResult:
    fixture = ToyHashSlhDsaHypertreeFixture.model_validate_json(
        path.read_text(encoding="utf-8")
    )

    digest_bytes = fixture.digest_bits // 8
    verified_fors_trees = 0
    for tree_index, leaf_hex in enumerate(fixture.fors_leaves_hex):
        node = bytes.fromhex(leaf_hex)
        index = fixture.fors_selected_indices[tree_index]
        for level, sibling_hex in enumerate(fixture.fors_auth_paths_hex[tree_index]):
            sibling = bytes.fromhex(sibling_hex)
            if index & 1:
                left, right = sibling, node
            else:
                left, right = node, sibling
            node = _fors_parent(
                tree_index=tree_index,
                level=level,
                left=left,
                right=right,
                digest_bytes=digest_bytes,
            )
            index >>= 1
        if node.hex() == fixture.fors_roots_hex[tree_index]:
            verified_fors_trees += 1

    verified_wots_chains = 0
    for chain_index, node_hex in enumerate(fixture.wots_signature_nodes_hex):
        node = bytes.fromhex(node_hex)
        for step_index in range(fixture.wots_remaining_steps[chain_index]):
            node = _chain_step(
                node=node,
                chain_index=chain_index,
                step_index=step_index,
                digest_bytes=digest_bytes,
            )
        if node.hex() == fixture.wots_public_key_roots_hex[chain_index]:
            verified_wots_chains += 1

    fors_aggregate = _slh_dsa_fors_aggregate(
        roots=[bytes.fromhex(value) for value in fixture.fors_roots_hex],
        digest_bytes=digest_bytes,
    )
    hypertree_node = _slh_dsa_hypertree_leaf(
        fors_aggregate=fors_aggregate,
        wots_roots=[
            bytes.fromhex(value) for value in fixture.wots_public_key_roots_hex
        ],
        digest_bytes=digest_bytes,
    )
    hypertree_index = fixture.hypertree_leaf_index
    for level, sibling_hex in enumerate(fixture.hypertree_auth_path_hex):
        sibling = bytes.fromhex(sibling_hex)
        if hypertree_index & 1:
            left, right = sibling, hypertree_node
        else:
            left, right = hypertree_node, sibling
        hypertree_node = _merkle_parent(
            left=left,
            right=right,
            level=level,
            digest_bytes=digest_bytes,
        )
        hypertree_index >>= 1

    return ToyHashSlhDsaHypertreeResult(
        verified=(
            verified_fors_trees == fixture.fors_tree_count
            and verified_wots_chains == fixture.wots_chain_count
            and hypertree_node.hex() == fixture.hypertree_root_hex
        ),
        target_name=fixture.target_name,
        digest_bits=fixture.digest_bits,
        hash_function=fixture.hash_function,
        signature_model=fixture.signature_model,
        fors_tree_count=fixture.fors_tree_count,
        fors_tree_height=fixture.fors_tree_height,
        fors_selected_indices=fixture.fors_selected_indices,
        verified_fors_trees=verified_fors_trees,
        wots_chain_count=fixture.wots_chain_count,
        wots_max_chain_steps=fixture.wots_max_chain_steps,
        verified_wots_chains=verified_wots_chains,
        hypertree_height=fixture.hypertree_height,
        hypertree_leaf_index=fixture.hypertree_leaf_index,
        public=fixture.public,
        security_claim=fixture.security_claim,
    )


def _chain_step(
    *,
    node: bytes,
    chain_index: int,
    step_index: int,
    digest_bytes: int,
) -> bytes:
    payload = (
        _CHAIN_DOMAIN
        + chain_index.to_bytes(2, "big")
        + step_index.to_bytes(2, "big")
        + node
    )
    return hashlib.shake_256(payload).digest(digest_bytes)


def _merkle_parent(
    *,
    left: bytes,
    right: bytes,
    level: int,
    digest_bytes: int,
) -> bytes:
    payload = _MERKLE_NODE_DOMAIN + level.to_bytes(2, "big") + left + right
    return hashlib.shake_256(payload).digest(digest_bytes)


def _fors_parent(
    *,
    tree_index: int,
    level: int,
    left: bytes,
    right: bytes,
    digest_bytes: int,
) -> bytes:
    payload = (
        _FORS_NODE_DOMAIN
        + tree_index.to_bytes(2, "big")
        + level.to_bytes(2, "big")
        + left
        + right
    )
    return hashlib.shake_256(payload).digest(digest_bytes)


def _slh_dsa_fors_aggregate(*, roots: list[bytes], digest_bytes: int) -> bytes:
    payload = _SLH_DSA_FORS_AGGREGATE_DOMAIN + b"".join(roots)
    return hashlib.shake_256(payload).digest(digest_bytes)


def _slh_dsa_hypertree_leaf(
    *,
    fors_aggregate: bytes,
    wots_roots: list[bytes],
    digest_bytes: int,
) -> bytes:
    payload = (
        _SLH_DSA_HYPERTREE_LEAF_DOMAIN
        + fors_aggregate
        + b"".join(wots_roots)
    )
    return hashlib.shake_256(payload).digest(digest_bytes)


def _validate_lowercase_hex(value: str) -> None:
    if value != value.lower():
        raise ValueError("hash values must be lowercase")
    try:
        bytes.fromhex(value)
    except ValueError as exc:
        raise ValueError("hash values must be valid hexadecimal") from exc
