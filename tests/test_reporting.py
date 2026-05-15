from agades_lwe_gym.reporting.markdown import render_report


def test_report_contains_mock_disclaimer_and_limitations() -> None:
    report = render_report(
        title="Toy Report",
        records=[
            {
                "candidate_id": "candidate-1",
                "evaluation": {
                    "valid": True,
                    "combined_score": -92.0,
                    "estimated_time_bits": 76.0,
                    "estimated_memory_bits": 28.0,
                    "estimator_name": "mock-lattice-estimator",
                },
            }
        ],
    )

    assert "Toy Report" in report
    assert "Mock Vs Real Estimator Status" in report
    assert "Limitations" in report
    assert "not a security claim" in report.lower()

