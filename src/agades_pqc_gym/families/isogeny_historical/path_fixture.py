from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from agades_pqc_gym.families.isogeny_historical.path_estimator import (
    TOY_ISOGENY_CASES,
    TOY_ISOGENY_MAX_BRANCHING_FACTOR,
    TOY_ISOGENY_MAX_VOLCANO_HEIGHT,
    TOY_ISOGENY_MAX_WALK_LENGTH,
    TOY_ISOGENY_VOLCANO_WALK_CASE,
)


class ToyIsogenyPathFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["agades.pqc.isogeny_historical_toy_path.v1"]
    family: Literal["ISOGENY_HISTORICAL"]
    target_name: str = Field(min_length=1)
    n: int = Field(gt=0, le=128)
    case: Literal[
        "toy_sidh_path_search",
        "toy_commutative_walk_search",
        "toy_volcano_walk_search",
    ]
    walk_length: int = Field(ge=1, le=TOY_ISOGENY_MAX_WALK_LENGTH)
    branching_factor: int = Field(ge=2, le=TOY_ISOGENY_MAX_BRANCHING_FACTOR)
    volcano_height: int | None = Field(
        default=None,
        ge=1,
        le=TOY_ISOGENY_MAX_VOLCANO_HEIGHT,
    )
    start_node: str = Field(min_length=1)
    end_node: str = Field(min_length=1)
    path: list[str] = Field(min_length=2)
    graph_edges: list[tuple[str, str]] | None = None
    node_levels: dict[str, int] | None = None
    historical_not_current: Literal[True]
    current_standard_claim: Literal[False]
    public: Literal[True]
    security_claim: Literal[False]

    @model_validator(mode="after")
    def validate_toy_path(self) -> ToyIsogenyPathFixture:
        if self.case not in TOY_ISOGENY_CASES:
            raise ValueError(
                "toy isogeny path fixture case must be one of "
                f"{', '.join(sorted(TOY_ISOGENY_CASES))}"
            )
        if len(self.path) != self.walk_length + 1:
            raise ValueError("toy isogeny path length must equal walk_length + 1")
        if self.path[0] != self.start_node:
            raise ValueError("toy isogeny path must start at start_node")
        if self.path[-1] != self.end_node:
            raise ValueError("toy isogeny path must end at end_node")
        if any(not node for node in self.path):
            raise ValueError("toy isogeny path nodes must be non-empty")
        if len(set(self.path)) != len(self.path):
            raise ValueError("toy isogeny path fixture must be a simple path")
        if self.case == TOY_ISOGENY_VOLCANO_WALK_CASE:
            _validate_volcano_fixture(self)
        elif (
            self.volcano_height is not None
            or self.graph_edges is not None
            or self.node_levels is not None
        ):
            raise ValueError(
                "toy isogeny non-volcano fixtures must not declare volcano graph data"
            )
        return self


class ToyIsogenyPathFixtureResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verified: bool
    target_name: str
    n: int
    case: str
    walk_length: int
    branching_factor: int
    volcano_height: int | None
    start_node: str
    end_node: str
    path: list[str]
    graph_edges: list[tuple[str, str]] | None
    node_levels: dict[str, int] | None
    historical_not_current: bool
    current_standard_claim: bool
    public: bool
    security_claim: bool


def verify_toy_isogeny_path_fixture(path: Path) -> ToyIsogenyPathFixtureResult:
    fixture = ToyIsogenyPathFixture.model_validate_json(
        path.read_text(encoding="utf-8")
    )
    verified = (
        len(fixture.path) == fixture.walk_length + 1
        and fixture.path[0] == fixture.start_node
        and fixture.path[-1] == fixture.end_node
        and len(set(fixture.path)) == len(fixture.path)
        and _volcano_graph_verified(fixture)
    )
    return ToyIsogenyPathFixtureResult(
        verified=verified,
        target_name=fixture.target_name,
        n=fixture.n,
        case=fixture.case,
        walk_length=fixture.walk_length,
        branching_factor=fixture.branching_factor,
        volcano_height=fixture.volcano_height,
        start_node=fixture.start_node,
        end_node=fixture.end_node,
        path=fixture.path,
        graph_edges=fixture.graph_edges,
        node_levels=fixture.node_levels,
        historical_not_current=fixture.historical_not_current,
        current_standard_claim=fixture.current_standard_claim,
        public=fixture.public,
        security_claim=fixture.security_claim,
    )


def _validate_volcano_fixture(fixture: ToyIsogenyPathFixture) -> None:
    if fixture.volcano_height is None:
        raise ValueError("toy volcano path fixture requires volcano_height")
    if fixture.graph_edges is None or not fixture.graph_edges:
        raise ValueError("toy volcano path fixture requires graph_edges")
    if fixture.node_levels is None or not fixture.node_levels:
        raise ValueError("toy volcano path fixture requires node_levels")
    for node in fixture.path:
        if node not in fixture.node_levels:
            raise ValueError("toy volcano path nodes must have levels")
        level = fixture.node_levels[node]
        if not 0 <= level <= fixture.volcano_height:
            raise ValueError("toy volcano path node levels must be in range")
    edge_set = _normalized_edge_set(fixture.graph_edges)
    for left, right in zip(fixture.path, fixture.path[1:], strict=False):
        if _normalized_edge(left, right) not in edge_set:
            raise ValueError("toy volcano path edges must connect the path")
        if abs(fixture.node_levels[left] - fixture.node_levels[right]) > 1:
            raise ValueError("toy volcano path levels must move by at most one")


def _volcano_graph_verified(fixture: ToyIsogenyPathFixture) -> bool:
    if fixture.case != TOY_ISOGENY_VOLCANO_WALK_CASE:
        return True
    if (
        fixture.volcano_height is None
        or fixture.graph_edges is None
        or fixture.node_levels is None
    ):
        return False
    edge_set = _normalized_edge_set(fixture.graph_edges)
    return all(
        _normalized_edge(left, right) in edge_set
        and abs(fixture.node_levels[left] - fixture.node_levels[right]) <= 1
        for left, right in zip(fixture.path, fixture.path[1:], strict=False)
    )


def _normalized_edge_set(edges: list[tuple[str, str]]) -> set[tuple[str, str]]:
    normalized_edges: set[tuple[str, str]] = set()
    for left, right in edges:
        if not left or not right or left == right:
            raise ValueError("toy volcano graph edges must connect distinct nodes")
        normalized_edges.add(_normalized_edge(left, right))
    return normalized_edges


def _normalized_edge(left: str, right: str) -> tuple[str, str]:
    return tuple(sorted((left, right)))
