from __future__ import annotations

from pathlib import Path

REQUIRED_CHECKED_RELEASE_COMMANDS = (
    "uv run agades-pqc hf-space-smoke --out reports/hf_space_smoke.json",
    "uv run agades-pqc hf-space-smoke-verify --report reports/hf_space_smoke.json",
    "uv run agades-pqc hf-space-remote-smoke --space-id "
    "AgadesTech/agades-pqc-gym-agent-env --out reports/hf_space_remote_smoke.json",
    "uv run agades-pqc hf-space-remote-smoke-verify "
    "--report reports/hf_space_remote_smoke.json",
    "uv run agades-pqc nvidia-manifest-safety "
    "--out reports/nvidia_manifest_safety.json",
    "uv run agades-pqc nvidia-manifest-safety-verify "
    "--report reports/nvidia_manifest_safety.json",
    "uv run agades-pqc prime-environment-smoke "
    "--out reports/prime_environment_smoke.json",
    "uv run agades-pqc prime-environment-smoke-verify "
    "--report reports/prime_environment_smoke.json",
    "uv run agades-pqc ecosystem-smoke --out reports/ecosystem_smoke.json",
    "uv run agades-pqc ecosystem-smoke-verify --report reports/ecosystem_smoke.json",
    "uv run agades-pqc release-artifacts --max-passes 6",
)
REQUIRED_CHECKED_REPORTS = (
    "reports/hf_space_smoke.json",
    "reports/hf_space_remote_smoke.json",
    "reports/nvidia_manifest_safety.json",
    "reports/prime_environment_smoke.json",
    "reports/ecosystem_smoke.json",
)


def _validation_commands() -> str:
    runbook = Path("docs/IMPLEMENT.md").read_text(encoding="utf-8")
    section_marker = "## Validation Commands\n\n```bash\n"
    section_start = runbook.index(section_marker) + len(section_marker)
    section_end = runbook.index("```", section_start)
    return runbook[section_start:section_end]


def test_implementation_runbook_lists_checked_release_gate_commands() -> None:
    commands = _validation_commands()

    missing = [
        command
        for command in REQUIRED_CHECKED_RELEASE_COMMANDS
        if command not in commands
    ]

    assert missing == []


def test_implementation_runbook_diff_check_covers_checked_reports() -> None:
    commands = _validation_commands()
    diff_check_lines = [
        line
        for line in commands.splitlines()
        if line.startswith("git diff --exit-code -- ")
    ]

    assert len(diff_check_lines) == 1
    missing = [
        report
        for report in REQUIRED_CHECKED_REPORTS
        if report not in diff_check_lines[0]
    ]

    assert missing == []
