from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

FitnessReportSchema = Literal["agades.pqc.fitness_report.v1"]
FITNESS_REPORT_SCHEMA: FitnessReportSchema = "agades.pqc.fitness_report.v1"


class FitnessReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: FitnessReportSchema = FITNESS_REPORT_SCHEMA
    combined_score: float
    estimated_time_bits: float | None
    estimated_memory_bits: float | None
    validity_score: float
    reproducibility_score: float
    novelty_score: float
    assumption_penalty: float
    instability_penalty: float

    def as_metrics(self) -> dict[str, float | str | None]:
        data = self.model_dump(mode="json")
        data["fitness_schema_version"] = data.pop("schema_version")
        return data
