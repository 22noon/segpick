"""
Tests for ReasoningExplorer.compare() provenance comparison.
"""

from __future__ import annotations

from segpick.explorer import ReasoningExplorer
from segpick.models import (
    BiologicalHypothesisNode,
    EvidencePatternNode,
    InterpretiveFindingNode,
    MeasurementNode,
    ObservationNode,
    ReasoningEdge,
    ReasoningGraph,
)


def _identical_provenance_graph():
    """Two hypotheses with identical provenance (same evidence chain)."""
    m = MeasurementNode("m1", "ch1", "metric", 1.0)
    o = ObservationNode("o1", "type1", "src1", "Obs")
    f = InterpretiveFindingNode("f1", "Finding", "Interp")
    s = EvidencePatternNode("s1", "p1", "Pattern", "Interp", "high")
    h1 = BiologicalHypothesisNode("h1", "Hypothesis 1", "Exp 1", "high")
    h2 = BiologicalHypothesisNode("h2", "Hypothesis 2", "Exp 2", "high")

    edges = (
        ReasoningEdge(h1.id, s.id, "supported_by"),
        ReasoningEdge(h2.id, s.id, "supported_by"),
        ReasoningEdge(s.id, f.id, "composed_from"),
        ReasoningEdge(f.id, o.id, "derived_from"),
        ReasoningEdge(o.id, m.id, "supported_by"),
    )

    return ReasoningGraph(
        measurements=(m,),
        observations=(o,),
        interpretive_findings=(f,),
        evidence_patterns=(s,),
        biological_hypotheses=(h1, h2),
        edges=edges,
    )


def _distinct_provenance_graph():
    """Two hypotheses with completely distinct provenance."""
    m1 = MeasurementNode("m1", "ch1", "metric1", 1.0)
    m2 = MeasurementNode("m2", "ch2", "metric2", 2.0)
    o1 = ObservationNode("o1", "type1", "src1", "Obs 1")
    o2 = ObservationNode("o2", "type2", "src2", "Obs 2")
    f1 = InterpretiveFindingNode("f1", "Finding 1", "Interp 1")
    f2 = InterpretiveFindingNode("f2", "Finding 2", "Interp 2")
    s1 = EvidencePatternNode("s1", "p1", "Pattern 1", "Interp 1", "high")
    s2 = EvidencePatternNode("s2", "p2", "Pattern 2", "Interp 2", "high")
    h1 = BiologicalHypothesisNode("h1", "Hypothesis 1", "Exp 1", "high")
    h2 = BiologicalHypothesisNode("h2", "Hypothesis 2", "Exp 2", "high")

    edges = (
        ReasoningEdge(h1.id, s1.id, "supported_by"),
        ReasoningEdge(s1.id, f1.id, "composed_from"),
        ReasoningEdge(f1.id, o1.id, "derived_from"),
        ReasoningEdge(o1.id, m1.id, "supported_by"),
        ReasoningEdge(h2.id, s2.id, "supported_by"),
        ReasoningEdge(s2.id, f2.id, "composed_from"),
        ReasoningEdge(f2.id, o2.id, "derived_from"),
        ReasoningEdge(o2.id, m2.id, "supported_by"),
    )

    return ReasoningGraph(
        measurements=(m1, m2),
        observations=(o1, o2),
        interpretive_findings=(f1, f2),
        evidence_patterns=(s1, s2),
        biological_hypotheses=(h1, h2),
        edges=edges,
    )


def _partially_shared_provenance_graph():
    """Two hypotheses sharing some but not all evidence."""
    m1 = MeasurementNode("m1", "ch1", "metric1", 1.0)
    m2 = MeasurementNode("m2", "ch2", "metric2", 2.0)
    m3 = MeasurementNode("m3", "ch3", "metric3", 3.0)
    o1 = ObservationNode("o1", "type1", "src1", "Shared Obs")
    o2 = ObservationNode("o2", "type2", "src2", "Unique to A")
    o3 = ObservationNode("o3", "type3", "src3", "Unique to B")
    f1 = InterpretiveFindingNode("f1", "Shared Finding", "Shared Interp")
    f2 = InterpretiveFindingNode("f2", "Finding A", "Interp A")
    f3 = InterpretiveFindingNode("f3", "Finding B", "Interp B")
    s1 = EvidencePatternNode("s1", "p1", "Shared Pattern", "Shared", "high")
    s2 = EvidencePatternNode("s2", "p2", "Pattern A", "A", "high")
    s3 = EvidencePatternNode("s3", "p3", "Pattern B", "B", "high")
    h1 = BiologicalHypothesisNode("h1", "Hypothesis A", "Exp A", "high")
    h2 = BiologicalHypothesisNode("h2", "Hypothesis B", "Exp B", "high")

    edges = (
        # A: h1 -> s1 -> f1 -> o1 -> m1
        # A: h1 -> s2 -> f2 -> o2 -> m2
        # B: h2 -> s1 -> f1 -> o1 -> m1 (shared)
        # B: h2 -> s3 -> f3 -> o3 -> m3
        ReasoningEdge(h1.id, s1.id, "supported_by"),
        ReasoningEdge(h1.id, s2.id, "supported_by"),
        ReasoningEdge(h2.id, s1.id, "supported_by"),
        ReasoningEdge(h2.id, s3.id, "supported_by"),
        ReasoningEdge(s1.id, f1.id, "composed_from"),
        ReasoningEdge(s2.id, f2.id, "composed_from"),
        ReasoningEdge(s3.id, f3.id, "composed_from"),
        ReasoningEdge(f1.id, o1.id, "derived_from"),
        ReasoningEdge(f2.id, o2.id, "derived_from"),
        ReasoningEdge(f3.id, o3.id, "derived_from"),
        ReasoningEdge(o1.id, m1.id, "supported_by"),
        ReasoningEdge(o2.id, m2.id, "supported_by"),
        ReasoningEdge(o3.id, m3.id, "supported_by"),
    )

    return ReasoningGraph(
        measurements=(m1, m2, m3),
        observations=(o1, o2, o3),
        interpretive_findings=(f1, f2, f3),
        evidence_patterns=(s1, s2, s3),
        biological_hypotheses=(h1, h2),
        edges=edges,
    )


def _shared_downstream_graph():
    """Two hypotheses sharing downstream evidence (same pattern/finding/obs/meas)."""
    m = MeasurementNode("m1", "ch1", "metric", 1.0)
    o = ObservationNode("o1", "type1", "src1", "Shared Obs")
    f = InterpretiveFindingNode("f1", "Shared Finding", "Shared Interp")
    s = EvidencePatternNode("s1", "shared_pattern", "Shared Pattern", "Shared", "high")
    h1 = BiologicalHypothesisNode("h1", "Hypothesis A", "Exp A", "high")
    h2 = BiologicalHypothesisNode("h2", "Hypothesis B", "Exp B", "high")

    edges = (
        ReasoningEdge(h1.id, s.id, "supported_by"),
        ReasoningEdge(h2.id, s.id, "supported_by"),
        ReasoningEdge(s.id, f.id, "composed_from"),
        ReasoningEdge(f.id, o.id, "derived_from"),
        ReasoningEdge(o.id, m.id, "supported_by"),
    )

    return ReasoningGraph(
        measurements=(m,),
        observations=(o,),
        interpretive_findings=(f,),
        evidence_patterns=(s,),
        biological_hypotheses=(h1, h2),
        edges=edges,
    )


def _conflicting_evidence_graph():
    """Hypothesis A supported by evidence, Hypothesis B contradicted by same evidence."""
    m = MeasurementNode("m1", "ch1", "metric", 1.0)
    o = ObservationNode("o1", "type1", "src1", "Obs")
    f = InterpretiveFindingNode("f1", "Finding", "Interp")
    s1 = EvidencePatternNode("s1", "p1", "Supporting Pattern", "Supports", "high")
    s2 = EvidencePatternNode("s2", "p2", "Contradicting Pattern", "Contradicts", "high")
    h1 = BiologicalHypothesisNode("h1", "Supported Hypothesis", "Exp 1", "high")
    h2 = BiologicalHypothesisNode("h2", "Contradicted Hypothesis", "Exp 2", "high")

    edges = (
        # h1 supported by s1
        ReasoningEdge(h1.id, s1.id, "supported_by"),
        # h2 contradicted by s2
        ReasoningEdge(h2.id, s2.id, "contradicted_by"),
        # Both patterns composed from same finding
        ReasoningEdge(s1.id, f.id, "composed_from"),
        ReasoningEdge(s2.id, f.id, "conflicted_by"),
        ReasoningEdge(f.id, o.id, "derived_from"),
        ReasoningEdge(o.id, m.id, "supported_by"),
    )

    return ReasoningGraph(
        measurements=(m,),
        observations=(o,),
        interpretive_findings=(f,),
        evidence_patterns=(s1, s2),
        biological_hypotheses=(h1, h2),
        edges=edges,
    )


def test_identical_provenance():
    """Two claims with identical downstream provenance share all evidence nodes/edges."""
    graph = _identical_provenance_graph()
    explorer = ReasoningExplorer(graph)

    cmp = explorer.compare("h1", "h2")

    # Claims are different but all downstream evidence is shared
    assert cmp.claim_a.id == "h1"
    assert cmp.claim_b.id == "h2"
    assert {n.id for n in cmp.common_nodes} == {"s1", "f1", "o1", "m1"}
    # Common edges: s1->f1, f1->o1, o1->m1 (3 edges; h1->s1 and h2->s1 differ in source)
    assert len(cmp.common_edges) == 3
    edge_keys = {(e.source_id, e.target_id, e.relationship) for e in cmp.common_edges}
    assert edge_keys == {
        ("s1", "f1", "composed_from"),
        ("f1", "o1", "derived_from"),
        ("o1", "m1", "supported_by"),
    }
    # Each claim has its own edge to the shared pattern
    assert len(cmp.unique_to_a_edges) == 1
    assert len(cmp.unique_to_b_edges) == 1
    assert cmp.unique_to_a_edges[0].source_id == "h1"
    assert cmp.unique_to_b_edges[0].source_id == "h2"


def test_distinct_provenance():
    """Two claims with completely distinct provenance share nothing."""
    graph = _distinct_provenance_graph()
    explorer = ReasoningExplorer(graph)

    cmp = explorer.compare("h1", "h2")

    assert cmp.claim_a.id == "h1"
    assert cmp.claim_b.id == "h2"
    assert len(cmp.common_nodes) == 0
    assert len(cmp.common_edges) == 0
    assert {n.id for n in cmp.unique_to_a_nodes} == {"h1", "s1", "f1", "o1", "m1"}
    assert {n.id for n in cmp.unique_to_b_nodes} == {"h2", "s2", "f2", "o2", "m2"}
    assert len(cmp.unique_to_a_edges) == 4
    assert len(cmp.unique_to_b_edges) == 4


def test_partially_shared_provenance():
    """Two claims sharing some evidence (shared pattern/finding/obs/meas)."""
    graph = _partially_shared_provenance_graph()
    explorer = ReasoningExplorer(graph)

    cmp = explorer.compare("h1", "h2")

    assert cmp.claim_a.id == "h1"
    assert cmp.claim_b.id == "h2"
    # Shared: s1, f1, o1, m1
    assert {n.id for n in cmp.common_nodes} == {"s1", "f1", "o1", "m1"}
    # Common edges among shared nodes
    assert len(cmp.common_edges) == 3
    # A unique: h1, s2, f2, o2, m2
    assert {n.id for n in cmp.unique_to_a_nodes} == {"h1", "s2", "f2", "o2", "m2"}
    # B unique: h2, s3, f3, o3, m3
    assert {n.id for n in cmp.unique_to_b_nodes} == {"h2", "s3", "f3", "o3", "m3"}


def test_shared_downstream_evidence():
    """Two claims sharing all downstream evidence from pattern down."""
    graph = _shared_downstream_graph()
    explorer = ReasoningExplorer(graph)

    cmp = explorer.compare("h1", "h2")

    assert cmp.claim_a.id == "h1"
    assert cmp.claim_b.id == "h2"
    # Everything except the claims is shared
    assert {n.id for n in cmp.common_nodes} == {"s1", "f1", "o1", "m1"}
    # Common edges among shared nodes: s1->f1, f1->o1, o1->m1
    assert len(cmp.common_edges) == 3
    edge_keys = {(e.source_id, e.target_id, e.relationship) for e in cmp.common_edges}
    assert edge_keys == {
        ("s1", "f1", "composed_from"),
        ("f1", "o1", "derived_from"),
        ("o1", "m1", "supported_by"),
    }
    # Only the claims themselves are unique (each has its own edge to s1)
    assert {n.id for n in cmp.unique_to_a_nodes} == {"h1"}
    assert {n.id for n in cmp.unique_to_b_nodes} == {"h2"}
    assert len(cmp.unique_to_a_edges) == 1  # h1 -> s1
    assert len(cmp.unique_to_b_edges) == 1  # h2 -> s1


def test_conflicting_supporting_evidence():
    """Hypothesis A supported, Hypothesis B contradicted by related evidence."""
    graph = _conflicting_evidence_graph()
    explorer = ReasoningExplorer(graph)

    cmp = explorer.compare("h1", "h2")

    assert cmp.claim_a.id == "h1"
    assert cmp.claim_b.id == "h2"
    # Shared downstream: f1, o1, m1
    assert {n.id for n in cmp.common_nodes} == {"f1", "o1", "m1"}
    # A unique: h1, s1 (supported_by)
    assert {n.id for n in cmp.unique_to_a_nodes} == {"h1", "s1"}
    # B unique: h2, s2 (contradicted_by)
    assert {n.id for n in cmp.unique_to_b_nodes} == {"h2", "s2"}
    # Edge relationships differ
    edge_rels_a = {e.relationship for e in cmp.unique_to_a_edges}
    edge_rels_b = {e.relationship for e in cmp.unique_to_b_edges}
    assert "supported_by" in edge_rels_a
    assert "contradicted_by" in edge_rels_b


def test_compare_raises_for_unknown_node():
    """compare() raises KeyError if either node doesn't exist."""
    graph = _identical_provenance_graph()
    explorer = ReasoningExplorer(graph)

    try:
        explorer.compare("h1", "nonexistent")
        raise AssertionError("Expected KeyError")
    except KeyError as exc:
        assert "Unknown reasoning node" in str(exc)

    try:
        explorer.compare("nonexistent", "h1")
        raise AssertionError("Expected KeyError")
    except KeyError as exc:
        assert "Unknown reasoning node" in str(exc)
