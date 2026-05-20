from __future__ import annotations

from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

EvaluatorResultSchema = Literal["agades.pqc.evaluator_result.v1"]
EVALUATOR_RESULT_SCHEMA: EvaluatorResultSchema = "agades.pqc.evaluator_result.v1"
EvaluationStatus = Literal["ok", "unsupported", "error"]


class EvaluatorResult(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_version: EvaluatorResultSchema = EVALUATOR_RESULT_SCHEMA
    evaluator_name: str = Field(
        validation_alias=AliasChoices("evaluator_name", "estimator_name")
    )
    evaluator_version: str | None = Field(
        validation_alias=AliasChoices("evaluator_version", "estimator_version")
    )
    evaluator_commit: str | None = Field(
        validation_alias=AliasChoices("evaluator_commit", "estimator_commit")
    )
    evaluation_status: EvaluationStatus = "ok"
    attack_type: str
    time_bits: float | None
    memory_bits: float | None
    success_probability: float | None = None
    raw_output: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)

    @property
    def estimator_name(self) -> str:
        return self.evaluator_name

    @property
    def estimator_version(self) -> str | None:
        return self.evaluator_version

    @property
    def estimator_commit(self) -> str | None:
        return self.evaluator_commit

    @model_validator(mode="after")
    def validate_status_payload(self) -> EvaluatorResult:
        if self.evaluation_status != "ok" and (
            self.time_bits is not None or self.memory_bits is not None
        ):
            raise ValueError(
                "unsupported/error evaluator results must not include "
                "time_bits or memory_bits"
            )
        return self
