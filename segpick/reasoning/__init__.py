"""Rule-based biological reasoning."""

from .builtin_rules import CANDIDATE_RULES, GENE_RULES
from .engine import evaluate_rule_set, evaluate_rules
from .graph import build_reasoning_graph
from .llm_bundle import (
    LLM_BUNDLE_VERSION,
    build_llm_reasoning_bundle,
    build_llm_review_package,
    load_llm_bundle_schema,
    load_llm_output_schema,
    write_llm_reasoning_bundle,
)
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
    "evaluate_rule_set",
    "load_active_rules",
    "load_rule_file",
    "merge_rules",
    "split_rules_by_scope",
    "build_reasoning_graph",
    "LLM_BUNDLE_VERSION",
    "build_llm_reasoning_bundle",
    "build_llm_review_package",
    "load_llm_bundle_schema",
    "load_llm_output_schema",
    "write_llm_reasoning_bundle",
]
