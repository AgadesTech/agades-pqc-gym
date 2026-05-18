from __future__ import annotations

from collections.abc import Iterator
from itertools import product
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_MQ_ASSIGNMENTS = 65_536


class ToyMQPolynomial(BaseModel):
    model_config = ConfigDict(extra="forbid")

    constant: int = Field(ge=0, le=1)
    linear: list[int]
    quadratic: list[tuple[int, int, int]] = Field(default_factory=list)


class ToyMQFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["agades.pqc.multivariate_toy_mq.v1"]
    family: Literal["MULTIVARIATE"]
    target_name: str = Field(min_length=1)
    variables: int = Field(gt=0)
    equations: int = Field(gt=0)
    field: Literal["GF(2)"]
    polynomials: list[ToyMQPolynomial] = Field(min_length=1)
    expected_solution: list[int] = Field(min_length=1)
    public: Literal[True]
    security_claim: Literal[False]

    @model_validator(mode="after")
    def validate_shape(self) -> ToyMQFixture:
        if self.equations != len(self.polynomials):
            raise ValueError("equations must equal polynomial count")
        if len(self.expected_solution) != self.variables:
            raise ValueError("expected_solution length must equal variables")
        if any(bit not in {0, 1} for bit in self.expected_solution):
            raise ValueError("expected_solution must be binary")
        for polynomial in self.polynomials:
            if len(polynomial.linear) != self.variables:
                raise ValueError("linear coefficient length must equal variables")
            if any(bit not in {0, 1} for bit in polynomial.linear):
                raise ValueError("linear coefficients must be binary")
            seen_terms: set[tuple[int, int]] = set()
            for left, right, coefficient in polynomial.quadratic:
                if coefficient not in {0, 1}:
                    raise ValueError("quadratic coefficients must be binary")
                if left < 0 or left >= self.variables:
                    raise ValueError("quadratic term index must be in range")
                if right < 0 or right >= self.variables:
                    raise ValueError("quadratic term index must be in range")
                term_key = (left, right)
                if term_key in seen_terms:
                    raise ValueError("quadratic terms must be unique")
                seen_terms.add(term_key)
        return self


class ToyMQSolution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    solved: bool
    target_name: str
    variables: int
    equations: int
    field_order: int
    assignment_count: int
    solution: list[int] | None
    public: bool
    security_claim: bool
    guessed_variables: int | None = None
    guess_count: int | None = None
    residual_variables: int | None = None
    max_residual_assignments_per_guess: int | None = None


def solve_toy_mq_fixture(path: Path) -> ToyMQSolution:
    fixture = ToyMQFixture.model_validate_json(path.read_text(encoding="utf-8"))
    return _solve_fixture(fixture)


def solve_toy_mq_hybrid_fixture(
    path: Path,
    *,
    guessed_variables: int,
) -> ToyMQSolution:
    fixture = ToyMQFixture.model_validate_json(path.read_text(encoding="utf-8"))
    if guessed_variables < 1 or guessed_variables >= fixture.variables:
        raise ValueError(
            "toy MQ hybrid fixture requires 1 <= guessed_variables < variables"
        )
    return _solve_fixture(fixture, guessed_variables=guessed_variables)


def _solve_fixture(
    fixture: ToyMQFixture,
    guessed_variables: int | None = None,
) -> ToyMQSolution:
    assignment_count = 2**fixture.variables
    if assignment_count > MAX_MQ_ASSIGNMENTS:
        raise ValueError(
            "toy MQ fixture exceeds exhaustive assignment limit: "
            f"{assignment_count}"
        )

    matches: list[list[int]] = []
    for candidate in _candidate_assignments(fixture, guessed_variables):
        if all(
            _evaluate_polynomial(polynomial, candidate) == 0
            for polynomial in fixture.polynomials
        ):
            matches.append(candidate)

    if len(matches) != 1:
        return _solution(
            fixture,
            assignment_count=assignment_count,
            solution=None,
            solved=False,
            guessed_variables=guessed_variables,
        )

    solution = matches[0]
    return _solution(
        fixture,
        assignment_count=assignment_count,
        solution=solution,
        solved=solution == fixture.expected_solution,
        guessed_variables=guessed_variables,
    )


def _candidate_assignments(
    fixture: ToyMQFixture,
    guessed_variables: int | None,
) -> Iterator[list[int]]:
    if guessed_variables is None:
        for assignment in product((0, 1), repeat=fixture.variables):
            yield list(assignment)
        return

    residual_variables = fixture.variables - guessed_variables
    for guess in product((0, 1), repeat=guessed_variables):
        for residual in product((0, 1), repeat=residual_variables):
            yield [*guess, *residual]


def _evaluate_polynomial(
    polynomial: ToyMQPolynomial,
    assignment: list[int],
) -> int:
    value = polynomial.constant
    for index, coefficient in enumerate(polynomial.linear):
        value ^= coefficient & assignment[index]
    for left, right, coefficient in polynomial.quadratic:
        value ^= coefficient & assignment[left] & assignment[right]
    return value


def _solution(
    fixture: ToyMQFixture,
    *,
    assignment_count: int,
    solution: list[int] | None,
    solved: bool,
    guessed_variables: int | None,
) -> ToyMQSolution:
    residual_variables = (
        fixture.variables - guessed_variables if guessed_variables is not None else None
    )
    return ToyMQSolution(
        solved=solved,
        target_name=fixture.target_name,
        variables=fixture.variables,
        equations=fixture.equations,
        field_order=2,
        assignment_count=assignment_count,
        solution=solution,
        public=fixture.public,
        security_claim=fixture.security_claim,
        guessed_variables=guessed_variables,
        guess_count=2**guessed_variables if guessed_variables is not None else None,
        residual_variables=residual_variables,
        max_residual_assignments_per_guess=(
            2**residual_variables if residual_variables is not None else None
        ),
    )
