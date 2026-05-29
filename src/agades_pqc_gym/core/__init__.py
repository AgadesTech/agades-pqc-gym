from agades_pqc_gym.core.assumptions import AssumptionSet
from agades_pqc_gym.core.attack_plan import (
    AttackOperator,
    AttackPlan,
    Claims,
    Constraints,
    Metadata,
)
from agades_pqc_gym.core.evaluator_result import EvaluatorResult
from agades_pqc_gym.core.family_adapter import (
    FamilyAdapter,
    ReproductionResult,
    ValidationFinding,
)
from agades_pqc_gym.core.family_plugin import (
    FamilyPluginDescriptor,
    FamilyPluginEntry,
)
from agades_pqc_gym.core.fitness import FitnessReport
from agades_pqc_gym.core.registry import FamilyRegistry, default_family_registry
from agades_pqc_gym.core.target import (
    Distribution,
    SupportLevel,
    TargetFamily,
    TargetSpec,
)
from agades_pqc_gym.core.trace_record import TraceRecord
from agades_pqc_gym.traces.redaction import redact_trace_record

__all__ = [
    "AssumptionSet",
    "AttackOperator",
    "AttackPlan",
    "Claims",
    "Constraints",
    "Distribution",
    "EvaluatorResult",
    "FamilyAdapter",
    "FamilyPluginDescriptor",
    "FamilyPluginEntry",
    "FamilyRegistry",
    "FitnessReport",
    "Metadata",
    "ReproductionResult",
    "ReportGenerator",
    "SupportLevel",
    "TargetFamily",
    "TargetSpec",
    "TraceRecord",
    "ValidationFinding",
    "default_family_registry",
    "redact_trace_record",
]


def __getattr__(name: str) -> object:
    if name == "ReportGenerator":
        from agades_pqc_gym.reporting.generator import ReportGenerator

        return ReportGenerator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
