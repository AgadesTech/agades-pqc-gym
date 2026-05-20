from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ToyUOVPolynomial(BaseModel):
    model_config = ConfigDict(extra="forbid")

    constant: int = Field(ge=0, le=1)
    linear: list[int]
    quadratic: list[tuple[int, int, int]] = Field(default_factory=list)


class ToyUOVPublicMapFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["agades.pqc.multivariate_toy_uov_public_map.v1"]
    family: Literal["MULTIVARIATE"]
    target_name: str = Field(min_length=1)
    variables: int = Field(gt=0)
    equations: int = Field(gt=0)
    field: Literal["GF(2)"]
    oil_variables: int = Field(gt=0)
    vinegar_variables: int = Field(gt=0)
    polynomials: list[ToyUOVPolynomial] = Field(min_length=1)
    signature: list[int] = Field(min_length=1)
    expected_output: list[int] = Field(min_length=1)
    public: Literal[True]
    security_claim: Literal[False]

    @model_validator(mode="after")
    def validate_shape(self) -> ToyUOVPublicMapFixture:
        if self.oil_variables + self.vinegar_variables != self.variables:
            raise ValueError(
                "toy UOV public-map fixture requires "
                "oil_variables + vinegar_variables == variables"
            )
        if self.equations != len(self.polynomials):
            raise ValueError("equations must equal polynomial count")
        if len(self.signature) != self.variables:
            raise ValueError("signature length must equal variables")
        _require_binary_vector(self.signature, name="signature")
        if len(self.expected_output) != self.equations:
            raise ValueError("expected_output length must equal equations")
        _require_binary_vector(self.expected_output, name="expected_output")
        for polynomial in self.polynomials:
            _validate_polynomial(polynomial, variables=self.variables)
        evaluated = _evaluate_public_map(self.polynomials, self.signature)
        if evaluated != self.expected_output:
            raise ValueError("signature does not evaluate to expected_output")
        return self


class ToyUOVPublicMapResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verified: bool
    target_name: str
    variables: int
    equations: int
    field_order: int
    oil_variables: int
    vinegar_variables: int
    signature: list[int]
    output: list[int]
    public: bool
    security_claim: bool


def verify_toy_uov_public_map_fixture(path: Path) -> ToyUOVPublicMapResult:
    fixture = ToyUOVPublicMapFixture.model_validate_json(
        path.read_text(encoding="utf-8")
    )
    output = _evaluate_public_map(fixture.polynomials, fixture.signature)
    return ToyUOVPublicMapResult(
        verified=output == fixture.expected_output,
        target_name=fixture.target_name,
        variables=fixture.variables,
        equations=fixture.equations,
        field_order=2,
        oil_variables=fixture.oil_variables,
        vinegar_variables=fixture.vinegar_variables,
        signature=fixture.signature,
        output=output,
        public=fixture.public,
        security_claim=fixture.security_claim,
    )


def _require_binary_vector(bits: list[int], *, name: str) -> None:
    if any(bit not in {0, 1} for bit in bits):
        raise ValueError(f"{name} must be binary")


def _validate_polynomial(polynomial: ToyUOVPolynomial, *, variables: int) -> None:
    if len(polynomial.linear) != variables:
        raise ValueError("linear coefficient length must equal variables")
    _require_binary_vector(polynomial.linear, name="linear coefficients")
    seen_terms: set[tuple[int, int]] = set()
    for left, right, coefficient in polynomial.quadratic:
        if coefficient not in {0, 1}:
            raise ValueError("quadratic coefficients must be binary")
        if left < 0 or left >= variables:
            raise ValueError("quadratic term index must be in range")
        if right < 0 or right >= variables:
            raise ValueError("quadratic term index must be in range")
        term_key = (left, right)
        if term_key in seen_terms:
            raise ValueError("quadratic terms must be unique")
        seen_terms.add(term_key)


def _evaluate_public_map(
    polynomials: list[ToyUOVPolynomial],
    signature: list[int],
) -> list[int]:
    return [
        _evaluate_polynomial(polynomial, signature)
        for polynomial in polynomials
    ]


def _evaluate_polynomial(
    polynomial: ToyUOVPolynomial,
    assignment: list[int],
) -> int:
    value = polynomial.constant
    for index, coefficient in enumerate(polynomial.linear):
        value ^= coefficient & assignment[index]
    for left, right, coefficient in polynomial.quadratic:
        value ^= coefficient & assignment[left] & assignment[right]
    return value
