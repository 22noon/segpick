"""Rule-based biological reasoning."""

from .builtin_rules import CANDIDATE_RULES, GENE_RULES
from .engine import evaluate_rules
from .rules import HypothesisRule, RuleCondition

__all__ = [
    "CANDIDATE_RULES",
    "GENE_RULES",
    "HypothesisRule",
    "RuleCondition",
    "evaluate_rules",
]
