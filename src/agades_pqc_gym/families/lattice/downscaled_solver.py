from __future__ import annotations

from itertools import product
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_BRUTE_FORCE_CANDIDATES = 65_536


class DownscaledLweFixture(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_version: Literal["agades.pqc.downscaled_lwe_instance.v1"]
    family: Literal["LWE"]
    target_name: str = Field(min_length=1)
    n: int = Field(gt=0)
    q: int = Field(gt=1)
    m: int = Field(gt=0)
    a_matrix: list[list[int]] = Field(alias="A", min_length=1)
    b_vector: list[int] = Field(alias="b", min_length=1)
    secret_domain: list[int] = Field(min_length=1)
    expected_secret: list[int] = Field(min_length=1)
    error_bound: int = Field(ge=0)
    public: Literal[True]
    security_claim: Literal[False]

    @model_validator(mode="after")
    def validate_dimensions(self) -> DownscaledLweFixture:
        if len(self.a_matrix) != self.m:
            raise ValueError("A row count must equal m")
        if len(self.b_vector) != self.m:
            raise ValueError("b length must equal m")
        if len(self.expected_secret) != self.n:
            raise ValueError("expected_secret length must equal n")
        if len(set(self.secret_domain)) != len(self.secret_domain):
            raise ValueError("secret_domain values must be unique")
        for row in self.a_matrix:
            if len(row) != self.n:
                raise ValueError("each A row length must equal n")
        return self


class DownscaledMlweFixture(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_version: Literal["agades.pqc.downscaled_mlwe_instance.v1"]
    family: Literal["MLWE"]
    target_name: str = Field(min_length=1)
    n: int = Field(gt=0)
    k: int = Field(gt=0)
    q: int = Field(gt=1)
    m: int = Field(gt=0)
    a_matrix: list[list[int]] = Field(alias="A", min_length=1)
    b_vector: list[int] = Field(alias="b", min_length=1)
    secret_domain: list[int] = Field(min_length=1)
    expected_secret: list[list[int]] = Field(min_length=1)
    error_bound: int = Field(ge=0)
    public: Literal[True]
    security_claim: Literal[False]

    @model_validator(mode="after")
    def validate_dimensions(self) -> DownscaledMlweFixture:
        if len(self.a_matrix) != self.m:
            raise ValueError("A row count must equal m")
        if len(self.b_vector) != self.m:
            raise ValueError("b length must equal m")
        if len(self.expected_secret) != self.k:
            raise ValueError("expected_secret row count must equal k")
        if len(set(self.secret_domain)) != len(self.secret_domain):
            raise ValueError("secret_domain values must be unique")
        for secret_row in self.expected_secret:
            if len(secret_row) != self.n:
                raise ValueError("each expected_secret row length must equal n")
        flat_dimension = self.k * self.n
        for row in self.a_matrix:
            if len(row) != flat_dimension:
                raise ValueError("each A row length must equal k * n")
        return self


class DownscaledLweSolution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    solved: bool
    target_name: str
    n: int
    q: int
    sample_count: int
    candidate_count: int
    secret: list[int] | None
    residuals: list[int]
    public: bool
    security_claim: bool


class DownscaledMlweSolution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    solved: bool
    target_name: str
    n: int
    k: int
    q: int
    sample_count: int
    candidate_count: int
    secret: list[list[int]] | None
    residuals: list[int]
    public: bool
    security_claim: bool


def solve_downscaled_lwe_fixture(path: Path) -> DownscaledLweSolution:
    fixture = DownscaledLweFixture.model_validate_json(path.read_text(encoding="utf-8"))
    candidate_count = len(fixture.secret_domain) ** fixture.n
    if candidate_count > MAX_BRUTE_FORCE_CANDIDATES:
        raise ValueError(
            "downscaled LWE fixture exceeds brute-force candidate limit: "
            f"{candidate_count}"
        )

    matches: list[tuple[list[int], list[int]]] = []
    for candidate in product(fixture.secret_domain, repeat=fixture.n):
        residuals = _centered_residuals(
            a_matrix=fixture.a_matrix,
            b_vector=fixture.b_vector,
            secret=list(candidate),
            q=fixture.q,
        )
        if all(abs(residual) <= fixture.error_bound for residual in residuals):
            matches.append((list(candidate), residuals))

    if len(matches) != 1:
        return _solution(
            fixture,
            candidate_count=candidate_count,
            secret=None,
            residuals=[],
            solved=False,
        )

    secret, residuals = matches[0]
    return _solution(
        fixture,
        candidate_count=candidate_count,
        secret=secret,
        residuals=residuals,
        solved=secret == fixture.expected_secret,
    )


def solve_downscaled_mlwe_fixture(path: Path) -> DownscaledMlweSolution:
    fixture = DownscaledMlweFixture.model_validate_json(
        path.read_text(encoding="utf-8")
    )
    flat_dimension = fixture.k * fixture.n
    candidate_count = len(fixture.secret_domain) ** flat_dimension
    if candidate_count > MAX_BRUTE_FORCE_CANDIDATES:
        raise ValueError(
            "downscaled MLWE fixture exceeds brute-force candidate limit: "
            f"{candidate_count}"
        )

    matches: list[tuple[list[list[int]], list[int]]] = []
    for candidate in product(fixture.secret_domain, repeat=flat_dimension):
        flat_secret = list(candidate)
        residuals = _centered_residuals(
            a_matrix=fixture.a_matrix,
            b_vector=fixture.b_vector,
            secret=flat_secret,
            q=fixture.q,
        )
        if all(abs(residual) <= fixture.error_bound for residual in residuals):
            matches.append(
                (_reshape_module_secret(flat_secret, fixture.k, fixture.n), residuals)
            )

    if len(matches) != 1:
        return _mlwe_solution(
            fixture,
            candidate_count=candidate_count,
            secret=None,
            residuals=[],
            solved=False,
        )

    secret, residuals = matches[0]
    return _mlwe_solution(
        fixture,
        candidate_count=candidate_count,
        secret=secret,
        residuals=residuals,
        solved=secret == fixture.expected_secret,
    )


def _centered_residuals(
    *,
    a_matrix: list[list[int]],
    b_vector: list[int],
    secret: list[int],
    q: int,
) -> list[int]:
    return [
        _center_mod(
            b_i - sum(a_ij * s_j for a_ij, s_j in zip(row, secret, strict=True)),
            q,
        )
        for row, b_i in zip(a_matrix, b_vector, strict=True)
    ]


def _center_mod(value: int, q: int) -> int:
    reduced = value % q
    if reduced > q // 2:
        return reduced - q
    return reduced


def _reshape_module_secret(flat_secret: list[int], k: int, n: int) -> list[list[int]]:
    return [flat_secret[offset : offset + n] for offset in range(0, k * n, n)]


def _solution(
    fixture: DownscaledLweFixture,
    *,
    candidate_count: int,
    secret: list[int] | None,
    residuals: list[int],
    solved: bool,
) -> DownscaledLweSolution:
    return DownscaledLweSolution(
        solved=solved,
        target_name=fixture.target_name,
        n=fixture.n,
        q=fixture.q,
        sample_count=fixture.m,
        candidate_count=candidate_count,
        secret=secret,
        residuals=residuals,
        public=fixture.public,
        security_claim=fixture.security_claim,
    )


def _mlwe_solution(
    fixture: DownscaledMlweFixture,
    *,
    candidate_count: int,
    secret: list[list[int]] | None,
    residuals: list[int],
    solved: bool,
) -> DownscaledMlweSolution:
    return DownscaledMlweSolution(
        solved=solved,
        target_name=fixture.target_name,
        n=fixture.n,
        k=fixture.k,
        q=fixture.q,
        sample_count=fixture.m,
        candidate_count=candidate_count,
        secret=secret,
        residuals=residuals,
        public=fixture.public,
        security_claim=fixture.security_claim,
    )
