import subprocess
import sys

from agades_pqc_gym import core
from agades_pqc_gym.core.family_plugin import FamilyPluginDescriptor, FamilyPluginEntry
from agades_pqc_gym.core.registry import FamilyRegistry, default_family_registry
from agades_pqc_gym.reporting import ReportGenerator
from agades_pqc_gym.traces.redaction import redact_trace_record


def test_report_generator_module_imports_without_core_public_api_cycle() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from agades_pqc_gym.reporting.generator import ReportGenerator; "
                "print(ReportGenerator.__name__)"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ReportGenerator"


def test_core_exports_family_agnostic_public_surface() -> None:
    assert core.ReportGenerator is ReportGenerator
    assert core.redact_trace_record is redact_trace_record
    assert {"ReportGenerator", "redact_trace_record"} <= set(core.__all__)


def test_core_exports_family_plugin_extension_surface() -> None:
    assert core.FamilyPluginDescriptor is FamilyPluginDescriptor
    assert core.FamilyPluginEntry is FamilyPluginEntry
    assert core.FamilyRegistry is FamilyRegistry
    assert core.default_family_registry is default_family_registry
    assert {
        "FamilyPluginDescriptor",
        "FamilyPluginEntry",
        "FamilyRegistry",
        "default_family_registry",
    } <= set(core.__all__)
