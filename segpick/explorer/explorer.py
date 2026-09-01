"""
Reasoning Explorer service.

This is the stable façade between consumers and the internal reasoning graph.
"""

from __future__ import annotations

from collections import defaultdict

from segpick.explorer.provenance import (
    ImpactPath,
    ImpactResult,
    NextEvidenceGap,
    NextEvidenceResult,
    Provenance,
    ProvenanceComparison,
)
from segpick.explorer.queries import PROVENANCE_RELATIONSHIPS, extract_provenance
from segpick.models import BiologicalFinding, EvidenceObservation
from segpick.models.reasoning_graph import ReasoningGraph
from segpick.reasoning import CANDIDATE_RULES, GENE_RULES


class ReasoningExplorer:
    """Public service for interrogating the reasoning graph."""

    def __init__(self, graph: ReasoningGraph):
        self._graph = graph

    def explain(self, node_id: str) -> Provenance:
        """Return the scientific justification for a reasoning node.

        Delegates to the provenance query engine to extract the minimal
        upstream justification graph for the given node.
        """
        return extract_provenance(self._graph, node_id)

    def compare(self, node_a: str, node_b: str) -> ProvenanceComparison:
        """Compare the reasoning supporting two nodes.

        Extracts provenance for both claims and performs a structural
        comparison of the justification graphs.

        Returns:
            ProvenanceComparison with common and unique nodes/edges.
        """
        prov_a = extract_provenance(self._graph, node_a)
        prov_b = extract_provenance(self._graph, node_b)

        # Use node IDs for structural comparison
        nodes_a = {n.id: n for n in prov_a.nodes}
        nodes_b = {n.id: n for n in prov_b.nodes}
        edges_a = {(e.source_id, e.target_id, e.relationship): e for e in prov_a.edges}
        edges_b = {(e.source_id, e.target_id, e.relationship): e for e in prov_b.edges}

        common_node_ids = set(nodes_a.keys()) & set(nodes_b.keys())
        unique_a_node_ids = set(nodes_a.keys()) - set(nodes_b.keys())
        unique_b_node_ids = set(nodes_b.keys()) - set(nodes_a.keys())

        common_edge_keys = set(edges_a.keys()) & set(edges_b.keys())
        unique_a_edge_keys = set(edges_a.keys()) - set(edges_b.keys())
        unique_b_edge_keys = set(edges_b.keys()) - set(edges_a.keys())

        return ProvenanceComparison(
            claim_a=prov_a.claim,
            claim_b=prov_b.claim,
            common_nodes=tuple(nodes_a[nid] for nid in sorted(common_node_ids)),
            common_edges=tuple(edges_a[k] for k in sorted(common_edge_keys)),
            unique_to_a_nodes=tuple(nodes_a[nid] for nid in sorted(unique_a_node_ids)),
            unique_to_a_edges=tuple(edges_a[k] for k in sorted(unique_a_edge_keys)),
            unique_to_b_nodes=tuple(nodes_b[nid] for nid in sorted(unique_b_node_ids)),
            unique_to_b_edges=tuple(edges_b[k] for k in sorted(unique_b_edge_keys)),
        )

    def impact(self, node_id: str) -> ImpactResult:
        """Return downstream consequences of a reasoning node.

        Follows reverse provenance edges (target -> source) from the given
        node to identify all higher-level reasoning nodes whose conclusions
        depend on it. Returns complete paths preserving edges and relationships.
        """
        # Build node index for lookup
        node_index = {
            node.id: node
            for collection in (
                self._graph.measurements,
                self._graph.observations,
                self._graph.interpretive_findings,
                self._graph.evidence_patterns,
                self._graph.biological_hypotheses,
                self._graph.scientific_conclusions,
            )
            for node in collection
        }

        if node_id not in node_index:
            raise KeyError(f"Unknown reasoning node '{node_id}'")

        # Build reverse adjacency: target_id -> list of (source_id, edge)
        reverse_adj = defaultdict(list)
        for edge in self._graph.provenance_edges():
            if edge.relationship in PROVENANCE_RELATIONSHIPS:
                reverse_adj[edge.target_id].append((edge.source_id, edge))

        # DFS from source to find all paths to claims (biological hypotheses AND scientific conclusions)
        # A claim is a biological hypothesis node or a scientific conclusion node
        claim_types = {n.id for n in self._graph.biological_hypotheses}
        claim_types.update(n.id for n in self._graph.scientific_conclusions)

        paths = []

        def dfs(current_id: str, path_nodes: list, path_edges: list):
            if current_id in claim_types:
                # Found a claim - record the path
                paths.append(ImpactPath(
                    claim=node_index[current_id],
                    nodes=tuple(node_index[nid] for nid in path_nodes + [current_id]),
                    edges=tuple(path_edges),
                ))
                # Continue searching to find paths to conclusions beyond this claim
                # (don't return early)

            for next_id, edge in reverse_adj.get(current_id, ()):
                dfs(next_id, path_nodes + [current_id], path_edges + [edge])

        dfs(node_id, [], [])

        return ImpactResult(
            source=node_index[node_id],
            paths=tuple(paths),
        )

    def next_evidence(self, node_id: str) -> NextEvidenceResult:
        """Return evidence gaps for a biological hypothesis.

        For a BiologicalHypothesisNode, uses the corresponding HypothesisRule
        from builtin rules to identify missing required and supporting evidence
        by checking against observations and findings in the reasoning graph.

        For non-hypothesis nodes, returns empty gaps (no rule evaluation exists).

        Raises:
            KeyError: If node_id does not exist in the graph.
        """
        # Find the node in the graph
        node_index = {
            node.id: node
            for collection in (
                self._graph.measurements,
                self._graph.observations,
                self._graph.interpretive_findings,
                self._graph.evidence_patterns,
                self._graph.biological_hypotheses,
            )
            for node in collection
        }

        if node_id not in node_index:
            raise KeyError(f"Unknown reasoning node '{node_id}'")

        node = node_index[node_id]

        # Only BiologicalHypothesisNode has rule_id
        if not hasattr(node, 'rule_id') or not node.rule_id:
            return NextEvidenceResult(
                hypothesis=node,
                rule_id="",
                missing_required=(),
                missing_supporting=(),
            )

        rule_id = node.rule_id

        # Find the matching HypothesisRule from builtin rules
        all_rules = CANDIDATE_RULES + GENE_RULES
        rule = next((r for r in all_rules if r.rule_id == rule_id), None)

        if rule is None:
            # Rule not found in builtin (could be user-defined) - return empty
            return NextEvidenceResult(
                hypothesis=node,
                rule_id=rule_id,
                missing_required=(),
                missing_supporting=(),
            )

        # Collect available observations and findings from the reasoning graph
        # Convert graph nodes to formats that RuleCondition.matches() expects
        observations = tuple(
            EvidenceObservation(
                observation_type=n.observation_type,
                source=n.source,
                description=n.description,
                severity=n.severity,
            )
            for n in self._graph.observations
        )
        findings = tuple(
            BiologicalFinding(
                category=n.category,
                title=n.title,
                severity=n.severity,
                confidence=n.confidence,
                scope=n.scope,
                summary=n.summary,
                sources=(n.source,),
            )
            for n in self._graph.interpretive_findings
        )

        # Check required conditions
        missing_required = []
        for condition in rule.requires:
            if not condition.matches(observations, findings):
                missing_required.append(NextEvidenceGap(
                    rule_id=rule_id,
                    condition=condition,
                    role="required",
                ))

        # Check supporting conditions
        missing_supporting = []
        for condition in rule.supports:
            if not condition.matches(observations, findings):
                missing_supporting.append(NextEvidenceGap(
                    rule_id=rule_id,
                    condition=condition,
                    role="supporting",
                ))

        return NextEvidenceResult(
            hypothesis=node,
            rule_id=rule_id,
            missing_required=tuple(missing_required),
            missing_supporting=tuple(missing_supporting),
        )
