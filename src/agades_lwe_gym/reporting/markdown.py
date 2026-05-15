from __future__ import annotations

from typing import Any


def render_report(title: str, records: list[dict[str, Any]]) -> str:
    rows = []
    estimator_names = set()
    for record in records:
        evaluation = record.get("evaluation", {})
        estimator_name = str(evaluation.get("estimator_name", "unknown"))
        estimator_names.add(estimator_name)
        row_template = (
            "| {candidate} | {valid} | {score} | {time} | {memory} | "
            "{estimator} |"
        )
        rows.append(
            row_template.format(
                candidate=record.get("candidate_id", "unknown"),
                valid=evaluation.get("valid", "unknown"),
                score=evaluation.get("combined_score", "unknown"),
                time=evaluation.get("estimated_time_bits", "unknown"),
                memory=evaluation.get("estimated_memory_bits", "unknown"),
                estimator=estimator_name,
            )
        )

    mock_status = (
        "At least one result uses the mock estimator. Mock output is not a security "
        "claim and exists only to verify evaluator plumbing."
        if any("mock" in name for name in estimator_names)
        else "No mock estimator records were detected in this report."
    )

    table = "\n".join(rows) if rows else "| none | n/a | n/a | n/a | n/a | n/a |"
    return (
        f"# {title}\n\n"
        "## Summary\n\n"
        "This report summarizes toy/downscaled AttackPlan evaluations.\n\n"
        "## Results\n\n"
        "| Candidate | Valid | Score | Time Bits | Memory Bits | Estimator |\n"
        "| --- | --- | ---: | ---: | ---: | --- |\n"
        f"{table}\n\n"
        "## Mock Vs Real Estimator Status\n\n"
        f"{mock_status}\n\n"
        "## Limitations\n\n"
        "Estimator outputs are hypotheses requiring independent review. This report is "
        "not a security claim, does not target live systems, and does not imply a "
        "break of any deployed post-quantum cryptographic standard.\n"
    )
