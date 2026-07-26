"""Rule-based biological reasoning."""

from .builtin_rules import CANDIDATE_RULES, GENE_RULES
from .engine import evaluate_rules
from .loader import (
    load_active_rules,
    load_rule_file,
    merge_rules,
    split_rules_by_scope,
)
from .rules import HypothesisRule, RuleCondition

__all__ = [
    "CANDIDATE_RULES",
    "GENE_RULES",
    "HypothesisRule",
    "RuleCondition",
    "evaluate_rules",
    "load_active_rules",
    "load_rule_file",
    "merge_rules",
    "split_rules_by_scope",
]
