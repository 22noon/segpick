"""
Reasoning graph query algorithms.
"""

from __future__ import annotations

from collections import defaultdict

from segpick.explorer.provenance import Provenance
from segpick.models.reasoning_graph import ReasoningGraph

PROVENANCE_RELATIONSHIPS = frozenset(
    {
        "supported_by",
        "derived_from",
        "composed_from",
        "contradicted_by",
        "conflicted_by",
    }
)


def extract_provenance(
    graph: ReasoningGraph,
    claim_id: str,
) -> Provenance:
    """
    Extract the minimal upstream provenance graph supporting a reasoning node.

    Edges in the reasoning graph flow from higher-level reasoning objects
    (biological hypotheses, evidence patterns, findings) to lower-level
    evidence (observations, measurements). This function traverses those
    edges in the forward direction (source_id -> target_id) to collect
    the complete justification chain for a claim.
    """

    node_index = {
        node.id: node
        for collection in (
            graph.measurements,
            graph.observations,
            graph.interpretive_findings,
            graph.evidence_patterns,
            graph.biological_hypotheses,
            graph.scientific_conclusions,
        )
        for node in collection
    }

    if claim_id not in node_index:
        raise KeyError(f"Unknown reasoning node '{claim_id}'")

    # Edges flow FROM higher-layer nodes TO lower-layer evidence
    # (source_id is the reasoning object, target_id is the evidence)
    outgoing = defaultdict(list)

    for edge in graph.provenance_edges():
        if edge.relationship in PROVENANCE_RELATIONSHIPS:
            outgoing[edge.source_id].append(edge)

    stack = [claim_id]

    visited: set[str] = set()

    nodes = []
    edges = []

    while stack:

        node_id = stack.pop()

        if node_id in visited:
            continue

        visited.add(node_id)

        nodes.append(node_index[node_id])

        for edge in outgoing.get(node_id, ()):

            edges.append(edge)

            stack.append(edge.target_id)

    return Provenance(
        claim=node_index[claim_id],
        nodes=tuple(nodes),
        edges=tuple(edges),
    )
