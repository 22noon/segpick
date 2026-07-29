from .engine import (
    ContributionSpec,
    CrossEvidenceContext,
    CrossEvidenceRule,
    RULE_REGISTRY,
    StructuredCrossEvidenceRule,
    discover_external_rules,
    evaluate_cross_evidence,
    register_rule,
)

__all__ = [
    "ContributionSpec",
    "CrossEvidenceContext",
    "CrossEvidenceRule",
    "RULE_REGISTRY",
    "StructuredCrossEvidenceRule",
    "discover_external_rules",
    "evaluate_cross_evidence",
    "register_rule",
]

# Register built-in reasoners.
from . import builtin as _builtin  # noqa: E402,F401
