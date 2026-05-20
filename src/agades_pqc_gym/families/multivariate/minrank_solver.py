from __future__ import annotations

from itertools import product
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_MINRANK_ASSIGNMENTS = 65_536
MAX_MINRANK_MATRIX_CELLS = 64


class ToyMinRankFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["agades.pqc.multivariate_toy_minrank.v1"]
    family: Literal["MULTIVARIATE"]
    target_name: str = Field(min_length=1)
    variables: int = Field(gt=0)
    equations: int = Field(gt=0)
    field: Literal["GF(2)"]
    matrix_rows: int = Field(gt=0)
    matrix_cols: int = Field(gt=0)
    target_rank: int = Field(ge=0)
    base_matrix: list[list[int]]
    coefficient_matrices: list[list[list[int]]] = Field(min_length=1)
    expected_solution: list[int] = Field(min_length=1)
    public: Literal[True]
    security_claim: Literal[False]

    @model_validator(mode="after")
    def validate_shape(self) -> ToyMinRankFixture:
        if self.equations != self.matrix_rows * self.matrix_cols:
            raise ValueError("equations must equal matrix_rows * matrix_cols")
        if self.matrix_rows * self.matrix_cols > MAX_MINRANK_MATRIX_CELLS:
            raise ValueError("toy MinRank matrix exceeds cell limit")
        if self.target_rank >= min(self.matrix_rows, self.matrix_cols):
            raise ValueError("target_rank must be smaller than matrix dimensions")
        if len(self.coefficient_matrices) != self.variables:
            raise ValueError("coefficient_matrices length must equal variables")
        if len(self.expected_solution) != self.variables:
            raise ValueError("expected_solution length must equal variables")
        if any(bit not in {0, 1} for bit in self.expected_solution):
            raise ValueError("expected_solution must be binary")
        _validate_matrix_shape(self.base_matrix, self.matrix_rows, self.matrix_cols)
        for matrix in self.coefficient_matrices:
            _validate_matrix_shape(matrix, self.matrix_rows, self.matrix_cols)
        return self


class ToyMinRankSolution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    solved: bool
    target_name: str
    variables: int
    equations: int
    field_order: int
    matrix_rows: int
    matrix_cols: int
    target_rank: int
    assignment_count: int
    solution: list[int] | None
    public: bool
    security_claim: bool


def solve_toy_minrank_fixture(path: Path) -> ToyMinRankSolution:
    fixture = ToyMinRankFixture.model_validate_json(path.read_text(encoding="utf-8"))
    assignment_count = 2**fixture.variables
    if assignment_count > MAX_MINRANK_ASSIGNMENTS:
        raise ValueError(
            "toy MinRank fixture exceeds exhaustive assignment limit: "
            f"{assignment_count}"
        )

    matches: list[list[int]] = []
    for assignment in product((0, 1), repeat=fixture.variables):
        candidate = list(assignment)
        matrix = _matrix_for_assignment(fixture, candidate)
        if _rank_gf2(matrix) <= fixture.target_rank:
            matches.append(candidate)

    if len(matches) != 1:
        return _solution(
            fixture,
            assignment_count=assignment_count,
            solution=None,
            solved=False,
        )

    solution = matches[0]
    return _solution(
        fixture,
        assignment_count=assignment_count,
        solution=solution,
        solved=solution == fixture.expected_solution,
    )


def _validate_matrix_shape(
    matrix: list[list[int]],
    rows: int,
    cols: int,
) -> None:
    if len(matrix) != rows:
        raise ValueError("matrix row count mismatch")
    for row in matrix:
        if len(row) != cols:
            raise ValueError("matrix column count mismatch")
        if any(bit not in {0, 1} for bit in row):
            raise ValueError("toy MinRank matrices must be binary")


def _matrix_for_assignment(
    fixture: ToyMinRankFixture,
    assignment: list[int],
) -> list[list[int]]:
    matrix = [row.copy() for row in fixture.base_matrix]
    for coefficient, coefficient_matrix in zip(
        assignment,
        fixture.coefficient_matrices,
        strict=True,
    ):
        if coefficient == 0:
            continue
        for row_index, row in enumerate(coefficient_matrix):
            for col_index, value in enumerate(row):
                matrix[row_index][col_index] ^= value
    return matrix


def _rank_gf2(matrix: list[list[int]]) -> int:
    rows = [row.copy() for row in matrix]
    if not rows:
        return 0
    row_count = len(rows)
    col_count = len(rows[0])
    rank = 0
    pivot_row = 0
    for col_index in range(col_count):
        pivot = next(
            (
                row_index
                for row_index in range(pivot_row, row_count)
                if rows[row_index][col_index] == 1
            ),
            None,
        )
        if pivot is None:
            continue
        rows[pivot_row], rows[pivot] = rows[pivot], rows[pivot_row]
        for row_index in range(row_count):
            if row_index != pivot_row and rows[row_index][col_index] == 1:
                rows[row_index] = [
                    left ^ right
                    for left, right in zip(
                        rows[row_index],
                        rows[pivot_row],
                        strict=True,
                    )
                ]
        rank += 1
        pivot_row += 1
        if pivot_row == row_count:
            break
    return rank


def _solution(
    fixture: ToyMinRankFixture,
    *,
    assignment_count: int,
    solution: list[int] | None,
    solved: bool,
) -> ToyMinRankSolution:
    return ToyMinRankSolution(
        solved=solved,
        target_name=fixture.target_name,
        variables=fixture.variables,
        equations=fixture.equations,
        field_order=2,
        matrix_rows=fixture.matrix_rows,
        matrix_cols=fixture.matrix_cols,
        target_rank=fixture.target_rank,
        assignment_count=assignment_count,
        solution=solution,
        public=fixture.public,
        security_claim=fixture.security_claim,
    )
