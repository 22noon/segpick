"""
Reasoning provenance.

A Provenance object is the minimal immutable justification graph for a
single reasoning claim. It is the canonical intermediate representation
returned by reasoning queries and consumed by higher-level projectors.

This class intentionally contains no traversal, rendering or interpretation
logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Provenance:
    """Minimal immutable justification graph for a single claim."""

    claim: Any
    nodes: tuple[Any, ...]
    edges: tuple[Any, ...]


@dataclass(frozen=True)
class ProvenanceComparison:
    """Structural comparison of two provenance graphs.

    Attributes:
        claim_a: The first claim node.
        claim_b: The second claim node.
        common_nodes: Nodes present in both provenance graphs.
        common_edges: Edges present in both provenance graphs.
        unique_to_a_nodes: Nodes only in the first provenance.
        unique_to_a_edges: Edges only in the first provenance.
        unique_to_b_nodes: Nodes only in the second provenance.
        unique_to_b_edges: Edges only in the second provenance.
    """

    claim_a: Any
    claim_b: Any
    common_nodes: tuple[Any, ...]
    common_edges: tuple[Any, ...]
    unique_to_a_nodes: tuple[Any, ...]
    unique_to_a_edges: tuple[Any, ...]
    unique_to_b_nodes: tuple[Any, ...]
    unique_to_b_edges: tuple[Any, ...]


@dataclass(frozen=True)
class ImpactPath:
    """A complete path from a source node to an affected claim.

    Attributes:
        claim: The affected claim node (e.g., BiologicalHypothesisNode).
        nodes: Ordered nodes along the path from source to claim (inclusive).
        edges: Ordered edges along the path from source to claim.
    """

    claim: Any
    nodes: tuple[Any, ...]
    edges: tuple[Any, ...]


@dataclass(frozen=True)
class ImpactResult:
    """Reverse-provenance traversal result identifying affected claims.

    Given a source node, follows reverse provenance edges to find all
    higher-level reasoning nodes whose conclusions depend on the source.

    Attributes:
        source: The node whose impact is being assessed.
        paths: Complete paths from source to each affected claim.
    """

    source: Any
    paths: tuple[ImpactPath, ...]


@dataclass(frozen=True, slots=True)
class NextEvidenceGap:
    """One missing piece of evidence that would advance a hypothesis rule.

    Attributes:
        rule_id: The hypothesis rule that needs this evidence.
        condition: The RuleCondition describing what is missing.
        role: "required" or "supporting" - whether the condition is mandatory or optional.
    """

    rule_id: str
    condition: Any  # RuleCondition from reasoning.rules
    role: str  # "required" | "supporting"


@dataclass(frozen=True, slots=True)
class NextEvidenceResult:
    """Evidence gaps for a biological hypothesis.

    Identifies missing required and supporting evidence from the
    corresponding HypothesisRule and its RuleEvaluation.

    Attributes:
        hypothesis: The BiologicalHypothesisNode being assessed.
        rule_id: The rule_id of the hypothesis.
        missing_required: Evidence gaps for mandatory conditions.
        missing_supporting: Evidence gaps for optional supporting conditions.
    """

    hypothesis: Any  # BiologicalHypothesisNode
    rule_id: str
    missing_required: tuple[NextEvidenceGap, ...]
    missing_supporting: tuple[NextEvidenceGap, ...]
